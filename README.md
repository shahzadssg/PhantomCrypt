# PhantomCrypt: Achieving Second-Order Deniability in Post-Quantum Covert Communication

PhantomCrypt is a novel cryptographic protocol designed to provide **second-order deniability** for covert communication. This means it protects against both passive surveillance (making hidden messages undetectable) and active coercion (allowing plausible deniable messages to be revealed).

Our Python implementation serves as a proof-of-concept, validating the practical feasibility and performance of PhantomCrypt's multi-layered encryption approach, which integrates post-quantum cryptography, information-theoretic secret sharing, and advanced steganography.

## Project Status

This is a **proof-of-concept implementation** to demonstrate PhantomCrypt's core principles and evaluate its performance characteristics. It's intended for research and educational purposes. While designed with strong cryptographic primitives, it's not yet hardened for production environments.

## Features

PhantomCrypt combines three key cryptographic primitives:

1.  **Invisible Encryption (IE)**: Embeds the true secret message within the statistical properties of a natural language cover text. This layer uses Shamir's threshold secret sharing, where shares are deterministically derived from selected words in the cover text based on a pre-shared master seed. This provides **existence deniability**, making the communication indistinguishable from innocent traffic.

2.  **False-Bottom Encryption (FBE)**: Creates multiple, independently decryptable decoy messages within a shared ciphertext container. These decoys are generated using linear equations over finite fields. Under coercion, parties can reveal these plausible decoy messages without compromising the true secret, offering **content deniability** with information-theoretic security guarantees.

3.  **Post-Quantum Key Encapsulation (PQC KEM)**: Protects all cryptographic materials against quantum adversaries. Our implementation simulates an ML-KEM-768-like KEM, aligning with NIST standardization efforts, to ensure **quantum resistance** for ephemeral session keys used in symmetric encryption.

In essence, PhantomCrypt offers:

*   **Dual Deniability**: Combines existence hiding and content deniability.
*   **Post-Quantum Security**: Future-proofs communication against quantum attacks.
*   **Steganographic Hiding**: Blends cryptographic material into innocuous-looking cover texts and standard encrypted traffic.
*   **Multi-Opening Security**: Allows for revealing multiple plausible decoy messages under duress.

## How it Works (Conceptual Overview)

Alice wants to send a secret message (`m_true`) to Bob.

1.  **IE Layer**: Alice selects a public cover text (e.g., a news article). Using a shared secret seed (`x_0`) with Bob, she deterministically selects words from the cover text. The hash values of these words, along with `m_true`, form points for a polynomial `P(x)`. An additional share `s_new` is computed from this polynomial.
2.  **FBE Layer**: Alice creates multiple believable decoy messages. These decoys are embedded into an FBE container, where each decoy has its own independent decryption key. This means different keys will decrypt the container to different plausible messages.
3.  **Hybrid Encryption Layer**:
    *   Alice encrypts the `s_new` (from IE) and the `x_0` seed using a session key derived from a PQC KEM.
    *   She then encrypts the FBE container (with its embedded decoys) using Alice's `s_new` as a key.
    *   The PQC KEM is used to encapsulate a session key for Bob.
    *   All these encrypted components are transmitted along with the *unmodified* cover text.

**To an outside observer**: The communication looks like standard hybrid encrypted traffic (a KEM-encapsulated key followed by symmetrically encrypted payloads) and a normal, publicly available cover text. There's nothing suspicious.

**Under coercion**: Bob can reveal a specific decoy message and its corresponding FBE decryption key. This revelation is designed to appear genuine, preventing the adversary from proving the existence of a true secret or other decoys.

**To reconstruct the true message**: Bob uses his secret key to decapsulate the PQC KEM, recover the session key, then decrypt `x_0` and `s_new`. With `x_0`, he regenerates the original shares from the cover text and, combined with `s_new`, reconstructs the polynomial `P(x)` to recover `m_true`.

## Implementation Details

This Python prototype is built with a focus on demonstrating the cryptographic mechanics and evaluating performance.

**Key Libraries:**

*   `galois`: For finite field arithmetic (GF(p)) and polynomial operations.
*   `cryptography`: For AES-256-GCM authenticated encryption and simulated PQC KEM operations.
*   `hashlib`: For SHA3-256 hash functions.
*   `os.urandom`: For cryptographically secure random number generation.
*   `numpy`: For array operations (dependency of `galois`).

**Configuration Parameters:**

Key parameters that influence security and performance, such as `IE_SECURITY_PARAM_T` (bit-length for prime `p`), `IE_THRESHOLD_K` (k-out-of-N secret sharing threshold), `IE_COVER_TEXT_LENGTH` (initial cover text length), and `FBE_NUM_DECOY_MESSAGES`, are configurable at the top of the main script for testing and benchmarking.

## Benchmarking Results (Summary from `run_table_ii_benchmarks`)

Our benchmarks demonstrate the practical feasibility of PhantomCrypt. Below are aggregated results for a typical configuration (`k=5`, `121` Cover Words, `3` Decoys, `100` Runs):

### Table II: PhantomCrypt Performance Benchmarks

| Operation                             | Mean Time (ms) | Std Dev (ms) | Complexity         |
| :------------------------------------ | :------------- | :----------- | :----------------- |
| **Setup & IE Layer Operations**       |                |              |                    |
| Setup (key generation)                | 2.22           | 0.71         | O(1)               |
| IE: Hash chain generation (k=5)       | 0.09           | 0.10         | O(k)               |
| IE: Word selection & hashing (k=5)    | 0.12           | 0.10         | O(k)               |
| IE: Polynomial interpolation (k=5)    | 5.06           | 1.91         | O(k²)              |
| **IE: Total Encryption (k=5)**        | **5.28**       | **1.92**     | **O(k²)**          |
| **FBE Layer Operations**              |                |              |                    |
| FBE: Container initialization         | 1.65           | 0.51         | O(n_init)          |
| FBE: Single decoy embedding           | 0.39           | 0.13         | O(k)               |
| FBE: 3 decoys embedding               | 1.40           | 0.55         | O(l*k)             |
| **Hybrid Layer Operations (Encryption)** |                |              |                    |
| Hybrid: KEM encapsulation             | 0.62           | 0.07         | KEM-specific       |
| Hybrid: AES encryption (share)        | 0.07           | 0.04         | O(n)               |
| Hybrid: AES encryption (container)    | 0.05           | 0.02         | O(\|\|c_FBE\|\|)       |
| **Hybrid: Total Encryption**          | **0.74**       | **0.08**     | **Dominated by KEM** |
| **Total Encryption Pipeline**         | **7.42**       | **2.00**     | **O(k² + KEM)**    |
| **Decryption Operations**             |                |              |                    |
| Decryption: KEM decapsulation         | 0.60           | 0.07         | KEM-specific       |
| Decryption: Share recovery            | 0.06           | 0.03         | O(k)               |
| Decryption: Polynomial reconstruction | 6.29           | 2.50         | O(k²)              |
| **Total True Message Decryption**     | **6.96**       | **2.50**     | **O(k²)**          |
| **Total Decoy Decryption**            | **0.66**       | **0.22**     | **O(k)**           |

**Key Findings:**

*   **Total Encryption Time (k=5):** 7.42 ms
*   **Total Decryption Time (k=5):** 6.96 ms
*   **Communication Overhead:** 1464 bytes (for 1 true, 3 decoys)
*   **Peak Memory Usage:** 0.18 MB
*   **Encryption/Decryption Ratio:** Approximately 1.1 times (encryption is slightly slower).

These figures indicate that PhantomCrypt is suitable for real-time covert communication, achieving overall encryption times well under 500ms. The PQC KEM simulation significantly contributes to the constant overhead, affirming its role in providing quantum resistance.

## Scalability Analysis (Summary from `run_table_iii_scalability`)

Scaling `k` (threshold) and `L` (cover text length) reveals performance trends:

### Table III: Performance Scaling with Threshold Parameter `k` (L Fixed for Consistency)

| k  | L (words) | Interpolation (ms) | Total Enc (ms) | Total Dec (ms) |
| :-- | :-------- | :----------------- | :------------- | :------------- |
| 3  | 100       | 2.02               | 5.11           | 2.96           |
| 5  | 200       | 6.78               | 8.95           | 5.18           |
| 7  | 300       | 9.18               | 12.59          | 10.36          |
| 10 | 500       | 20.86              | 24.08          | 22.08          |
| 15 | 1000      | 50.24              | 55.30          | 50.47          |

*   **Polynomial Interpolation (O(k²))**: As `k` increases, interpolation time grows super-linearly, becoming the dominant factor in both encryption and decryption.
*   **Overall Time**: Total encryption and decryption times increase with `k`, though decryption remains slightly faster for smaller `k`. For `k=15`, they are nearly symmetric.

This demonstrates the performance trade-offs associated with selecting `k`, where `k ∈ [5, 7]` offers a good balance between security (brute-force complexity Ω(2λ)) and efficiency.

## Communication Overhead Analysis (Summary from `run_table_iv_memory`)

### Table IV: PhantomCrypt Communication Overhead

| Component                   | Size (bytes) | Notes                                           |
| :-------------------------- | :----------- | :---------------------------------------------- |
| C_kem                       | 1088         | ML-KEM-768 ciphertext                           |
| C_1 (enc. share + seed)     | 92           | Enc(x_0 || s_new) + tag + nonce                 |
| C_2 (enc. FBE container)    | 284          | Enc(FBE data) + tag + nonce                     |
| **Total Communicated Data** | **1464**     | With 3 decoys                                   |
| Cover text (T)              | *0           | Transmitted separately or already public        |

*   *Cover text is transmitted through a separate channel or is already public; it's not counted as cryptographic overhead.*

The total transmitted cryptographic data (1464 bytes for 3 decoys) is largely constant and does not scale with the size of the covert message itself, which is crucial for steganographic efficiency. The PQC KEM ciphertext is the most significant individual component, underscoring its role in quantum resistance.

## Getting Started

To run the PhantomCrypt demonstration and benchmarks:

1.  **Clone this repository:**
    ```bash
    git clone <repository-url>
    cd PhantomCrypt
    ```
    (Replace `<repository-url>` with the actual URL)

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (You'll need `galois`, `numpy`, `cryptography`, etc.)

3.  **Execute the main script:**
    ```bash
    python phantomcrypt_main.py
    ```

The script will first run the performance benchmarks (Table II, III, IV) and then proceed with a narrative demonstration of PhantomCrypt's multi-layered encryption and decryption process, including the adversarial analysis scenario.

## Directory Structure

*   `phantomcrypt_main.py`: The main script that orchestrates the protocol, benchmarks, and narrative demo.
*   `requirements.txt`: Lists the Python dependencies.
*   (Potentially other modules if the implementation is split further, e.g., `phantomcrypt/ie.py`, `phantomcrypt/fbe.py`)

## Future Work & Limitations

As a proof-of-concept, PhantomCrypt has areas for future development:

*   **Multi-message security**: Formal CPA/CCA security definitions for repeated encryptions and provably secure seed evolution mechanisms are crucial for real-world scenarios.
*   **Active attack resistance**: Enhanced deniability against message injection or tampering.
*   **Advanced steganographic encoding**: Embedding shares in semantic features or grammatical structures for greater robustness against rephrasing attacks.
*   **Formal verification**: Machine-checked proofs using tools like Coq or Isabelle for enhanced assurance.
*   **Hardware acceleration**: Performance optimization via hardware acceleration, FFT-based polynomial evaluation, and precomputation techniques.
*   **Real-world deployment studies**: User studies, network analysis for detectability, and legal implications.
*   **Constant-time implementation**: Address timing side-channels in polynomial interpolation to prevent leakage.
*   **Secure RNGs**: Ensure all random values are generated using cryptographically secure pseudorandom number generators (CSPRNGs) validated by statistical tests.

