"""
Quantum Digital Signature (QDS) Engine
Simulates Bell State Entanglement, Quantum Teleportation, Pauli Correction,
and Multi-Basis Quantum Measurements (X, Y, Z).
Designed for SIH 2026 - Problem Statement SIH26141.
"""

import numpy as np
import hashlib
import time
import secrets
from typing import Dict, List, Tuple, Any

# Define Single-Qubit Basis States
KET_0 = np.array([1.0, 0.0], dtype=complex)
KET_1 = np.array([0.0, 1.0], dtype=complex)
KET_PLUS = (KET_0 + KET_1) / np.sqrt(2)
KET_MINUS = (KET_0 - KET_1) / np.sqrt(2)
KET_PLUS_I = (KET_0 + 1j * KET_1) / np.sqrt(2)
KET_MINUS_I = (KET_0 - 1j * KET_1) / np.sqrt(2)

# Pauli Matrices
I_GATE = np.array([[1, 0], [0, 1]], dtype=complex)
X_GATE = np.array([[0, 1], [1, 0]], dtype=complex)  # Bit-flip
Z_GATE = np.array([[1, 0], [0, -1]], dtype=complex) # Phase-flip
Y_GATE = np.array([[0, -1j], [1j, 0]], dtype=complex)
H_GATE = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2) # Hadamard

# 2-Qubit Gates
CNOT_GATE = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex)

class QuantumEngine:
    """
    Simulates core quantum operations needed for Quantum Digital Signatures:
    - Bell state |Φ+⟩ creation
    - Quantum Teleportation with classical communication
    - Pauli X and Z reconstruction
    - Measurement in X, Y, and Z bases
    """

    @staticmethod
    def create_bell_pair() -> np.ndarray:
        """
        Creates the Bell State |Φ+⟩ = (|00⟩ + |11⟩) / √2
        Returns a 4-element statevector.
        """
        state_00 = np.array([1, 0, 0, 0], dtype=complex)
        # Apply H to qubit 0: (H ⊗ I)
        h_tensor_i = np.kron(H_GATE, I_GATE)
        step1 = np.dot(h_tensor_i, state_00)
        # Apply CNOT: control=0, target=1
        bell_phi_plus = np.dot(CNOT_GATE, step1)
        return bell_phi_plus

    @staticmethod
    def encode_qubit(bit: int, basis: str = 'Z') -> np.ndarray:
        """
        Encodes a classical bit (0 or 1) into a quantum state vector in the given basis ('X', 'Y', 'Z').
        """
        if basis == 'Z':
            return KET_0 if bit == 0 else KET_1
        elif basis == 'X':
            return KET_PLUS if bit == 0 else KET_MINUS
        elif basis == 'Y':
            return KET_PLUS_I if bit == 0 else KET_MINUS_I
        else:
            raise ValueError(f"Unknown basis: {basis}")

    @staticmethod
    def measure_qubit(state: np.ndarray, basis: str = 'Z') -> Tuple[int, np.ndarray]:
        """
        Measures a single qubit state in the requested basis ('X', 'Y', or 'Z').
        Returns (outcome_bit: 0 or 1, collapsed_state).
        """
        # Ensure state is normalized
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm

        # Projective measurement
        if basis == 'Z':
            prob_0 = np.abs(np.vdot(KET_0, state)) ** 2
            prob_1 = np.abs(np.vdot(KET_1, state)) ** 2
            outcome = 0 if np.random.rand() < prob_0 / (prob_0 + prob_1) else 1
            collapsed = KET_0 if outcome == 0 else KET_1

        elif basis == 'X':
            prob_plus = np.abs(np.vdot(KET_PLUS, state)) ** 2
            prob_minus = np.abs(np.vdot(KET_MINUS, state)) ** 2
            outcome = 0 if np.random.rand() < prob_plus / (prob_plus + prob_minus) else 1
            collapsed = KET_PLUS if outcome == 0 else KET_MINUS

        elif basis == 'Y':
            prob_plus_i = np.abs(np.vdot(KET_PLUS_I, state)) ** 2
            prob_minus_i = np.abs(np.vdot(KET_MINUS_I, state)) ** 2
            outcome = 0 if np.random.rand() < prob_plus_i / (prob_plus_i + prob_minus_i) else 1
            collapsed = KET_PLUS_I if outcome == 0 else KET_MINUS_I
        else:
            raise ValueError(f"Unknown basis: {basis}")

        return outcome, collapsed

    @staticmethod
    def teleport_qubit(psi: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Full Quantum Teleportation Protocol:
        - Alice has state |psi⟩ (qubit 0)
        - Alice & Bob share Bell pair |Φ+⟩ (qubit 1: Alice, qubit 2: Bob)
        - 3-Qubit initial state: |psi⟩ ⊗ |Φ+⟩
        - Alice applies CNOT(0 -> 1) then H(0)
        - Alice measures qubits 0 and 1 -> gets classical bits (m1, m2)
        - Bob applies Pauli corrections: Z^m1 X^m2 to qubit 2
        - Output is Bob's reconstructed qubit (mathematically identical to |psi⟩)
        """
        # Step 1: Shared Bell pair between Alice (q1) and Bob (q2)
        bell = QuantumEngine.create_bell_pair() # 4-element vector (q1, q2)
        # Total 3-qubit state: q0 ⊗ q1 ⊗ q2 (8-element vector)
        state = np.kron(psi, bell)

        # Step 2: Alice applies CNOT on (q0 -> q1)
        # CNOT(0->1) ⊗ I(2)
        cnot_01_tensor_i2 = np.kron(CNOT_GATE, I_GATE)
        state = np.dot(cnot_01_tensor_i2, state)

        # Step 3: Alice applies Hadamard on q0: H ⊗ I ⊗ I
        h_tensor_i_i = np.kron(H_GATE, np.kron(I_GATE, I_GATE))
        state = np.dot(h_tensor_i_i, state)

        # Step 4: Alice measures q0 and q1 in Bell basis
        # Probabilities for 4 possible Bell measurement outcomes: (0,0), (0,1), (1,0), (1,1)
        probs = np.zeros(4)
        for i in range(4):
            # outcome i: q0 = (i >> 1) & 1, q1 = i & 1
            # subvector for Bob's q2 is indices [2*i, 2*i + 1]
            probs[i] = np.sum(np.abs(state[2*i : 2*i + 2]) ** 2)

        probs = probs / np.sum(probs)
        outcome = np.random.choice(4, p=probs)
        m1 = (outcome >> 1) & 1  # Alice's measurement on q0
        m2 = outcome & 1         # Alice's measurement on q1

        # Bob's unnormalized qubit state after Alice's measurement
        bob_raw = state[2*outcome : 2*outcome + 2]
        bob_state = bob_raw / np.linalg.norm(bob_raw)

        # Step 5: Bob applies Pauli correction: Z^m1 * X^m2
        correction = np.eye(2, dtype=complex)
        if m2 == 1:
            correction = np.dot(X_GATE, correction) # Bit flip
        if m1 == 1:
            correction = np.dot(Z_GATE, correction) # Phase flip

        bob_final = np.dot(correction, bob_state)
        # Remove global phase factor for clean statevector comparison
        if np.abs(bob_final[0]) > 1e-6:
            bob_final = bob_final * (np.conj(bob_final[0]) / np.abs(bob_final[0]))

        return bob_final, (int(m1), int(m2))

    @staticmethod
    def generate_qds_keypair(length: int = 16) -> Dict[str, Any]:
        """
        Generates classical-quantum key material for Quantum Digital Signatures:
        - Private Key: Sequence of bits and chosen bases (X, Y, Z)
        - Public Key / Quantum Template: Verification states
        """
        bases_choices = ['Z', 'X', 'Y']
        secret_bits = [int(secrets.randbelow(2)) for _ in range(length)]
        secret_bases = [str(np.random.choice(bases_choices)) for _ in range(length)]
        
        # Prepare quantum states
        quantum_states = [QuantumEngine.encode_qubit(b, base) for b, base in zip(secret_bits, secret_bases)]

        return {
            "length": length,
            "private_bits": secret_bits,
            "private_bases": secret_bases,
            "quantum_states": quantum_states
        }
