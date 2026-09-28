"""
Attack Simulation Module for Quantum Digital Signatures (QDS)
Simulates:
1. Channel Manipulation (Intercept-Resend / Eavesdropping)
2. Signature Forgery (Tampered payload / fake signature states)
3. Sender Impersonation (Rogue entity lacking legitimate entangled keys)
4. Replay Attack (Resending previously captured legitimate signature)
"""

import numpy as np
import time
import copy
from typing import List, Dict, Any, Tuple
from core.quantum_engine import QuantumEngine, X_GATE, Z_GATE, Y_GATE

class AttackSimulator:
    """
    Applies real-world cyber threat vectors directly to the quantum and classical channels.
    Provides clear, beginner-friendly explanations of how each attack operates.
    """

    @staticmethod
    def apply_ambient_channel_noise(states: List[np.ndarray], noise_rate: float = 0.02) -> List[np.ndarray]:
        """
        Simulates natural imperfections in physical fiber optic channels (depolarizing noise).
        noise_rate: Probability (0.0 to 0.15) of random phase/bit fluctuations.
        """
        noisy_states = []
        for state in states:
            s = state.copy()
            if np.random.rand() < noise_rate:
                # Random Pauli error (bit-flip, phase-flip, or both)
                pauli_gates = [X_GATE, Z_GATE, Y_GATE]
                gate = pauli_gates[np.random.randint(len(pauli_gates))]
                s = np.dot(gate, s)
            noisy_states.append(s)
        return noisy_states

    @staticmethod
    def simulate_eavesdropping(states: List[np.ndarray], intercept_prob: float = 1.0) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Scenario 1: Channel Manipulation / Intercept-Resend (Man-In-The-Middle)
        Eve intercepts qubits in transit, measures them in a randomly guessed basis,
        and resends the collapsed state to Bob.
        
        Because of the No-Cloning Theorem, measuring in the wrong basis alters the state,
        introducing a distinctive ~25% QBER spike.
        """
        modified_states = []
        bases_guessed = []
        qubits_intercepted = 0
        
        for state in states:
            if np.random.rand() < intercept_prob:
                qubits_intercepted += 1
                eve_basis = np.random.choice(['X', 'Z', 'Y'])
                bases_guessed.append(eve_basis)
                # Eve measures and collapses the qubit
                _, collapsed_state = QuantumEngine.measure_qubit(state, basis=eve_basis)
                modified_states.append(collapsed_state)
            else:
                modified_states.append(state.copy())

        explanation = (
            f"Eve intercepted {qubits_intercepted} flying quantum states and measured them in "
            f"random bases. In quantum physics, measuring an unknown quantum state permanently "
            f"collapses it (No-Cloning Theorem). This disturbance creates detectable anomalies!"
        )

        return modified_states, {
            "attack_name": "Channel Manipulation / Eavesdropping",
            "type": "MITM_INTERCEPT_RESEND",
            "qubits_intercepted": qubits_intercepted,
            "plain_explanation": explanation
        }

    @staticmethod
    def simulate_forgery(
        message: str,
        states: List[np.ndarray],
        tamper_message: bool = True
    ) -> Tuple[str, List[np.ndarray], Dict[str, Any]]:
        """
        Scenario 2: Signature Forgery
        Attacker alters the signed document (e.g. changing 'Pay $100' to 'Pay $1,000,000')
        or creates a fabricated signature using randomly guessed quantum states.
        """
        tampered_msg = message + " [FORGED / ALTERED PAYLOAD]" if tamper_message else message
        
        # Replace authentic states with random forged states
        forged_states = []
        for _ in states:
            random_bit = np.random.randint(0, 2)
            random_basis = np.random.choice(['X', 'Y', 'Z'])
            forged_states.append(QuantumEngine.encode_qubit(random_bit, random_basis))

        explanation = (
            "Attacker modified the original message text and fabricated counterfeit quantum "
            "signature states. Because the attacker lacks Alice's private key, the reconstructed "
            "quantum states cannot match Alice's verification baseline."
        )

        return tampered_msg, forged_states, {
            "attack_name": "Signature Forgery",
            "type": "FORGERY",
            "original_message": message,
            "tampered_message": tampered_msg,
            "plain_explanation": explanation
        }

    @staticmethod
    def simulate_impersonation(
        states: List[np.ndarray],
        pauli_corrections: List[Tuple[int, int]]
    ) -> Tuple[List[np.ndarray], List[Tuple[int, int]], Dict[str, Any]]:
        """
        Scenario 3: Sender Impersonation
        A rogue entity attempts to pose as Alice, transmitting arbitrary quantum states
        and fabricated classical Pauli correction outcomes without shared entanglement.
        """
        # Impersonator generates random garbage correction bits and random states
        fake_states = [QuantumEngine.encode_qubit(np.random.randint(0, 2), np.random.choice(['X', 'Z', 'Y'])) for _ in states]
        fake_corrections = [(np.random.randint(0, 2), np.random.randint(0, 2)) for _ in pauli_corrections]

        explanation = (
            "Rogue sender attempted to impersonate Alice. Without the genuine pre-shared "
            "entangled Bell pairs, the Pauli correction operations ($X^a Z^b$) fail completely, "
            "resulting in ~50% random error rate."
        )

        return fake_states, fake_corrections, {
            "attack_name": "Sender Impersonation",
            "type": "IMPERSONATION",
            "plain_explanation": explanation
        }

    @staticmethod
    def simulate_replay_attack(
        valid_signature_packet: Dict[str, Any],
        time_delay_seconds: float = 300.0
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Scenario 4: Replay Attack
        Attacker captures a genuinely valid signature packet from the past and replays it
        at a later time to authorize an action again.
        """
        replayed_packet = copy.deepcopy(valid_signature_packet)
        # The replayed packet contains the old timestamp and old nonce
        replayed_packet["timestamp"] = valid_signature_packet["timestamp"] - time_delay_seconds
        replayed_packet["is_replayed"] = True

        explanation = (
            f"Attacker captured a genuine, valid signature from earlier and attempted to replay it "
            f"{int(time_delay_seconds)} seconds later. The threat detector's nonce freshness and "
            f"timestamp window instantly flag this re-transmission."
        )

        return replayed_packet, {
            "attack_name": "Replay Attack",
            "type": "REPLAY",
            "delay_seconds": time_delay_seconds,
            "plain_explanation": explanation
        }
