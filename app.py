"""
Flask Web Application for User-Defined Quantum Digital Signature (QDS) Simulation
SIH 2026 - Problem Statement SIH26141
Team: Quantam Astra
"""

import os
import time
import secrets
import hashlib
from flask import Flask, render_template, request, jsonify
from core.quantum_engine import QuantumEngine
from core.attack_simulator import AttackSimulator
from core.threat_detector import ThreatDetector

app = Flask(__name__)
detector = ThreatDetector(qber_threshold=0.11, max_time_window_sec=60.0)

# In-memory store for recent signature nonces and demo packets
valid_demo_packet = None
valid_demo_template = None
valid_demo_message = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/simulate', methods=['POST'])
def simulate():
    global valid_demo_packet, valid_demo_template, valid_demo_message

    data = request.get_json() or {}
    message = data.get("message", "Authorize Critical Transaction #9921").strip()
    if not message:
        message = "Authorize Critical Transaction #9921"
        
    qubit_count = int(data.get("qubit_count", 16))
    qubit_count = max(4, min(qubit_count, 32))  # Keep in reasonable range
    
    ambient_noise = float(data.get("ambient_noise", 2)) / 100.0  # e.g. 2% -> 0.02
    threshold = float(data.get("threshold", 11)) / 100.0        # e.g. 11% -> 0.11
    attack_type = data.get("attack_type", "NONE")               # NONE, MITM, FORGERY, IMPERSONATION, REPLAY

    # STEP 1: Alice generates QDS Keypair and Quantum States
    keypair = QuantumEngine.generate_qds_keypair(length=qubit_count)
    alice_states = keypair["quantum_states"]

    # STEP 2: Alice teleports signature states using Bell Pairs
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

    # Store genuine packet for potential replay attack simulation
    if attack_type == "NONE":
        valid_demo_packet = signature_packet
        valid_demo_template = keypair
        valid_demo_message = message

    # STEP 3: Apply User-Selected Attack
    attack_meta = {
        "attack_name": "Authentic / Legitimate Transmission",
        "type": "NONE",
        "plain_explanation": "Alice signed and teleported the document normally. Only minor ambient fiber noise exists."
    }

    transmitted_packet = signature_packet
    transmitted_message = message

    if attack_type == "MITM":
        # Channel manipulation / intercept-resend
        modified_states, attack_meta = AttackSimulator.simulate_eavesdropping(channel_states, intercept_prob=1.0)
        transmitted_packet["quantum_states"] = modified_states

    elif attack_type == "FORGERY":
        # Alter message and forge states
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
        if valid_demo_packet is not None:
            transmitted_packet, attack_meta = AttackSimulator.simulate_replay_attack(valid_demo_packet, time_delay_seconds=300.0)
            transmitted_message = valid_demo_message
        else:
            transmitted_packet, attack_meta = AttackSimulator.simulate_replay_attack(signature_packet, time_delay_seconds=300.0)

    # STEP 4: Bob's Threat Detection Engine
    verification_result = detector.verify_signature(
        message=transmitted_message,
        signature_packet=transmitted_packet,
        expected_template=keypair if attack_type != "REPLAY" or valid_demo_template is None else valid_demo_template,
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
    detector.reset_nonces()
    return jsonify({"status": "success", "message": "Replay nonce history cleared."})

if __name__ == '__main__':
    # Start local web server
    print("Starting Quantam Astra QDS Threat Detection Server at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
