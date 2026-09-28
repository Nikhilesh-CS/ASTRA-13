"""
Flask Web Application for User-Defined Quantum Digital Signature (QDS) Simulation
SIH 2026 - Problem Statement SIH26141
Team: Quantam Astra
"""

import os
import time
import secrets
import hashlib
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, session
from core.quantum_engine import QuantumEngine
from core.attack_simulator import AttackSimulator
from core.threat_detector import ThreatDetector

app = Flask(__name__)
# Generate secret key for secure per-user session tracking
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# Limit maximum request body size to 64 KB to prevent DoS
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

# Per-session simulation state store with TTL cleanup
# Structure: { session_id: { "detector": ThreatDetector, "valid_demo_packet": ..., "valid_demo_template": ..., "valid_demo_message": ..., "last_active": timestamp } }
_SESSION_STORE: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 3600  # 1 hour TTL

def _clean_expired_sessions() -> None:
    """Removes stale sessions older than TTL to prevent memory leaks."""
    now = time.time()
    expired = [sid for sid, data in _SESSION_STORE.items() if now - data.get("last_active", 0) > SESSION_TTL_SECONDS]
    for sid in expired:
        _SESSION_STORE.pop(sid, None)

def _get_or_create_user_session() -> Dict[str, Any]:
    """Retrieves or creates isolated session-specific simulation state."""
    _clean_expired_sessions()
    
    if "session_id" not in session:
        session["session_id"] = secrets.token_hex(16)
        
    sid = session["session_id"]
    if sid not in _SESSION_STORE:
        _SESSION_STORE[sid] = {
            "detector": ThreatDetector(qber_threshold=0.11, max_time_window_sec=60.0),
            "valid_demo_packet": None,
            "valid_demo_template": None,
            "valid_demo_message": "",
            "last_active": time.time()
        }
    else:
        _SESSION_STORE[sid]["last_active"] = time.time()
        
    return _SESSION_STORE[sid]

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "Request payload too large. Maximum allowed size is 64KB."}), 413

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request format or payload."}), 400

@app.route('/')
def index():
    # Ensure session exists upon loading the page
    _get_or_create_user_session()
    return render_template('index.html')

@app.route('/api/simulate', methods=['POST'])
def simulate():
    user_state = _get_or_create_user_session()
    detector: ThreatDetector = user_state["detector"]

    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body format."}), 400

    # 1. Validate 'message'
    raw_message = data.get("message", "Authorize Critical Transaction #9921")
    if not isinstance(raw_message, str):
        return jsonify({"error": "Message must be a string."}), 400
    
    message = raw_message.strip()
    if len(message) > 5000:
        return jsonify({"error": "Message exceeds maximum length of 5000 characters."}), 400
    if not message:
        message = "Authorize Critical Transaction #9921"

    # 2. Validate 'qubit_count' (Allowed: 8 to 32)
    raw_qubits = data.get("qubit_count", 16)
    try:
        qubit_count = int(raw_qubits)
        if not (8 <= qubit_count <= 32):
            return jsonify({"error": "Invalid qubit_count. Must be an integer between 8 and 32."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "qubit_count must be a valid integer."}), 400

    # 3. Validate 'ambient_noise' (Allowed: 0 to 15 percent)
    raw_noise = data.get("ambient_noise", 2)
    try:
        ambient_noise_val = float(raw_noise)
        if not (0.0 <= ambient_noise_val <= 15.0):
            return jsonify({"error": "Invalid ambient_noise. Must be a number between 0 and 15."}), 400
        ambient_noise = ambient_noise_val / 100.0
    except (ValueError, TypeError):
        return jsonify({"error": "ambient_noise must be a valid number."}), 400

    # 4. Validate 'threshold' (Allowed: 5 to 25 percent)
    raw_threshold = data.get("threshold", 11)
    try:
        threshold_val = float(raw_threshold)
        if not (5.0 <= threshold_val <= 25.0):
            return jsonify({"error": "Invalid threshold. Must be a number between 5 and 25."}), 400
        threshold = threshold_val / 100.0
    except (ValueError, TypeError):
        return jsonify({"error": "threshold must be a valid number."}), 400

    # 5. Validate 'attack_type'
    allowed_attacks = {"NONE", "MITM", "FORGERY", "IMPERSONATION", "REPLAY"}
    attack_type = str(data.get("attack_type", "NONE")).upper().strip()
    if attack_type not in allowed_attacks:
        return jsonify({"error": f"Invalid attack_type. Must be one of: {', '.join(sorted(allowed_attacks))}."}), 400

    # =========================================================================
    # STEP 1: Alice generates QDS Keypair and Quantum States
    # =========================================================================
    keypair = QuantumEngine.generate_qds_keypair(length=qubit_count)
    alice_states = keypair["quantum_states"]

    # =========================================================================
    # STEP 2: Alice teleports signature states using Bell Pairs
    # =========================================================================
    teleported_states = []
    pauli_corrections = []
    for state in alice_states:
        reconstructed_state, correction_bits = QuantumEngine.teleport_qubit(state)
        teleported_states.append(reconstructed_state)
        pauli_corrections.append(correction_bits)

    # Apply ambient physical fiber noise
    channel_states = AttackSimulator.apply_ambient_channel_noise(teleported_states, noise_rate=ambient_noise)

    # Compute genuine signature packet
    timestamp = time.time()
    nonce = secrets.token_hex(8)
    message_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()

    signature_packet = {
        "message": message,
        "message_hash": message_hash,
        "nonce": nonce,
        "timestamp": timestamp,
        "quantum_states": channel_states,
        "pauli_corrections": pauli_corrections,
        "is_replayed": False
    }

    # Store genuine packet in user's isolated session for replay attack simulation
    if attack_type == "NONE":
        user_state["valid_demo_packet"] = signature_packet
        user_state["valid_demo_template"] = keypair
        user_state["valid_demo_message"] = message

    # =========================================================================
    # STEP 3: Apply User-Selected Attack Scenario
    # =========================================================================
    attack_meta = {
        "attack_name": "Authentic Transmission",
        "type": "NONE",
        "plain_explanation": "Alice signed and teleported the document normally. Only background fiber noise is present."
    }

    transmitted_packet = signature_packet
    transmitted_message = message

    if attack_type == "MITM":
        # Channel manipulation / intercept-resend
        modified_states, attack_meta = AttackSimulator.simulate_eavesdropping(channel_states, intercept_prob=1.0)
        transmitted_packet["quantum_states"] = modified_states

    elif attack_type == "FORGERY":
        # Alter message payload and forge quantum states
        tampered_msg, forged_states, attack_meta = AttackSimulator.simulate_forgery(message, channel_states)
        transmitted_message = tampered_msg
        transmitted_packet["quantum_states"] = forged_states

    elif attack_type == "IMPERSONATION":
        # Rogue sender without shared Bell pairs
        fake_states, fake_corrections, attack_meta = AttackSimulator.simulate_impersonation(channel_states, pauli_corrections)
        transmitted_packet["quantum_states"] = fake_states
        transmitted_packet["pauli_corrections"] = fake_corrections

    elif attack_type == "REPLAY":
        # Replay past packet or re-submit current packet with expired timestamp
        prior_packet = user_state.get("valid_demo_packet")
        prior_message = user_state.get("valid_demo_message", message)
        
        if prior_packet is not None:
            transmitted_packet, attack_meta = AttackSimulator.simulate_replay_attack(prior_packet, time_delay_seconds=300.0)
            transmitted_message = prior_message
        else:
            transmitted_packet, attack_meta = AttackSimulator.simulate_replay_attack(signature_packet, time_delay_seconds=300.0)

    # =========================================================================
    # STEP 4: Bob's Threat Detection Engine (Deterministic & Explainable)
    # =========================================================================
    verification_template = keypair
    if attack_type == "REPLAY" and user_state.get("valid_demo_template") is not None:
        verification_template = user_state["valid_demo_template"]

    verification_result = detector.verify_signature(
        message=transmitted_message,
        signature_packet=transmitted_packet,
        expected_template=verification_template,
        custom_threshold=threshold
    )

    # Response payload formatted for clean visualization in UI
    response = {
        "config": {
            "message": transmitted_message,
            "original_message": message,
            "qubit_count": qubit_count,
            "ambient_noise_percent": round(ambient_noise * 100, 1),
            "threshold_percent": round(threshold * 100, 1),
            "attack_type": attack_type
        },
        "attack_info": attack_meta,
        "verification": verification_result,
        "alice_summary": {
            "message_hash": message_hash,
            "nonce": nonce,
            "bases_used": keypair["private_bases"],
            "bits_encoded": keypair["private_bits"]
        }
    }

    return jsonify(response)

@app.route('/api/reset-nonce', methods=['POST'])
def reset_nonce():
    """Resets the replay nonce cache for the current user session only."""
    user_state = _get_or_create_user_session()
    user_state["detector"].reset_nonces()
    return jsonify({"status": "success", "message": "Session replay history reset successfully."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Quantam Astra QDS Threat Detection Server at http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)
