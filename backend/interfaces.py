from dataclasses import dataclass
from typing import List

@dataclass
class BloomFilterPayload:
    bit_array: List[int]       # Raw 0/1 array for TFHE encryption
    num_hashes: int            # |Hash| parameter (e.g., 5 or 10)
    size: int                  # |BF| bit length

@dataclass
class ThresholdResult:
    token_k_server: str        # Secret token K held by Server (Student B)
    token_k_prime_client: str  # Decrypted K' for Client (Student A); equals K iff count >= t
    fhe_latency_ms: float
    ciphertext_preview: str    # Hex snippet for the UI Adversary Inspector