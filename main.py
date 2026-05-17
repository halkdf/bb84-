import base64
import numpy as np

from braket.circuits import noises
from braket.devices import LocalSimulator

from utils.bb84 import initialize_protocol, encode_qubits, measure_qubits, filter_qubits, array_to_string
from utils.golay_code import GolayCode
from utils.secret_utils import convert_to_octets 

BIT_FLIP_PROBABILITY = 0.1 
NUMBER_OF_QUBITS = 12
ERROR_CORRECTION_CHUNK_SIZE = 12

alice_raw_key = np.array([])
bob_raw_key = np.array([])

while len(alice_raw_key) < ERROR_CORRECTION_CHUNK_SIZE:
    # Phase 1: Initialize quantum states and bases
    encoding_basis_A, states_A, _ = initialize_protocol(NUMBER_OF_QUBITS)
    sent_bits = array_to_string(states_A)
    _, _, measurement_basis_B = initialize_protocol(NUMBER_OF_QUBITS)
     # Phase 2: Quantum state preparation and transmission
    encoded_qubits_A = encode_qubits(NUMBER_OF_QUBITS, states_A, encoding_basis_A)
    noise = noises.BitFlip(probability=BIT_FLIP_PROBABILITY)
    encoded_qubits_A.apply_gate_noise(noise)
     # Phase 3: Measurement
    measured_circuit = measure_qubits(encoded_qubits_A, measurement_basis_B)
    device = LocalSimulator("braket_dm")
    result = device.run(measured_circuit, shots=1).result()
    measured_bits = list(result.measurements[0])
     # Phase 4: Basis reconciliation and key sifting
    alice_raw_key = np.concatenate((alice_raw_key, filter_qubits(sent_bits, encoding_basis_A, measurement_basis_B)))
    bob_raw_key = np.concatenate((bob_raw_key, filter_qubits(measured_bits, encoding_basis_A, measurement_basis_B)))

alice_raw_key = alice_raw_key[:12] 
alice_raw_key

bob_raw_key = bob_raw_key[:12] 
bob_raw_key

error_correcting_code = GolayCode()
generator_matrix = error_correcting_code.get_generator_matrix()
parity_check = error_correcting_code.get_parity_check_matrix()
b_matrix = error_correcting_code.get_b_matrix()

encoded_key_A = np.matmul(generator_matrix, alice_raw_key) % 2
syndrome_A = np.matmul(encoded_key_A, parity_check) % 2
parity_bits = encoded_key_A[12:]

print(f'Key of Alice after encoding is: {encoded_key_A}')
print(f'Syndrome of Alice (should be all zero): {syndrome_A}')
print(f'Information sent to Bob: {parity_bits}')

encoded_key_B = np.concatenate((bob_raw_key, parity_bits))
syndrome_B = np.matmul(encoded_key_B, parity_check) % 2
syndrome_BB = np.matmul(syndrome_B, b_matrix) % 2

print(f"Encoded key at Bob's: {encoded_key_B}")
print(f"First syndrome: {syndrome_B}")
print(f"Second syndrome: {syndrome_BB}")

if syndrome_BB.sum() < 4:
    correction_mask = np.concatenate((syndrome_BB, np.zeros(12,)))
    print(correction_mask)
else:
    print("Decoding failed - more than 3 errors")

corrected_key = np.mod(bob_raw_key + correction_mask[:12], 2)
corrected_key

corrected_key == alice_raw_key












