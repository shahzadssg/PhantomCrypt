# PhantomCrypt

A deniable-encryption scheme that combines **content deniability** and **existence deniability** under a **post-quantum envelope**. PhantomCrypt is research code accompanying the paper *PhantomCrypt: Composing Existence and Content Deniability under a Post-Quantum Envelope*.

---

## What it does

PhantomCrypt protects a message against an adversary who can both **observe the channel** and later **coerce the user** into handing over keys. It targets two distinct properties at once:

- **Content deniability (CD)** -- via *False-Bottom Encryption (FBE)*. The true message `m*` and `ℓ` decoy messages are packed into a single container `c_FBE` with `ℓ+1` structurally **symmetric** keys. Given the container and all keys, an adversary cannot tell which opening was the intended one.
- **Existence deniability (ED)** -- via *Invisible Encryption (IE)*. A share `s_new` is derived from an **unmodified** cover text and is uniform over the field, so it is indistinguishable from legitimate protocol randomness.
- **Post-quantum transport** -- both halves are wrapped in a hybrid **ML-KEM-768 + AES-256-GCM** envelope, producing `C = (C_kem, C₁, C₂, IV₁, IV₂)`, object-indistinguishable from a standard reference distribution.

The field is `p = 2²⁵⁶ − 2³² − 977`.

### The seed drives two independent derivations

This detail is load-bearing and easy to miss when reading the code:

- **Ordinates.** A PRNG seeded by `x₀` selects `k−1` cover words; each is hashed to a share value `s_j = H(w_{i_j})`.
- **Abscissae.** A *separate* hash chain on the same seed, `x_j = H(x_{j−1})`, produces the evaluation points, continued past used values to a fresh `x_new = H^k(x₀)`.

Given the cover text, these two are independent, which is exactly what the security argument for CD rests on. A cover dominated by one repeated word collapses the ordinates and leaves only one source of randomness. See *condition 4* below.

**A gotcha in the code.** `ie_abscissae` implements the chain and is the default. The small-field experiments (`p = 251`, needed for full seed enumeration) pass `absc_fn=ie_abscissae_indexed` instead, because at that field size a chain enters a cycle almost immediately and every seed reads as degenerate. That is an artifact of the experiment, not of the construction: at 256 bits the expected cycle length is about `2^128`. Section 6.3 of the notebook checks that the two derivations agree statistically on coverage, so the choice is not load-bearing for the threshold results.

### Key roles under coercion

The scheme has **four** algorithms, `(Setup, Enc, AddDecoy, Dec)`, with a **single** decryption algorithm. This is deliberate: a syntax with separate `DecTrue`/`DecDecoy` procedures would name a true opening in its own specification, and a coercer who reads the spec could demand it be run.

| Object | Lives where | Under coercion |
| --- | --- | --- |
| `sk_den = (x₀, k)` | pre-shared, memorised, **never written to the device** | withheld; there is no on-device object to demand |
| `dk_i = (sk_kem, sk_FBE,i)` | on the device, `ℓ+1` of them | all surrendered |

`Dec(PP, k, C, τ)` takes one key slot and one arity. On `sk_den` it returns `m*`; on `dk_i` it returns `m_i`. Nothing in a call records which kind of key went in. The true message is *dual-embedded*: reachable through the IE channel with `sk_den`, and also through the FBE container under `dk₀`, which is structurally identical to the `ℓ` decoy keys.

In code this is a single `Key` dataclass carrying `sk_kem` plus *either* the seed *or* an FBE key, one `Dec(ct, key)`, and a `CoercionDisclosure` object holding only the ciphertext and the `ℓ+1` decoy keys. Modelling the disclosure explicitly matters: an earlier version of the notebook passed a secrets bundle containing the seed into the coerced-opening path, which is not what coercion yields. The end-to-end cell asserts `sk_den` is absent from the disclosure and prints the number of distinct decryption procedures used, which is 1.

---

## Repository layout

| File | What it is |
| --- | --- |
| `PhantomCrypt_implementation.ipynb` | Reference implementation + evaluation (construction, coverage, anonymity-set concentration, feasibility threshold, growing-`k` timings, wire sizes, byte-distribution detector). |
| `admissibility_check.ipynb` | Tests the cover-admissibility predicate on real text. **Conditions 1--3 only** -- see below. |
| `build_corpus.ipynb` | Builds `corpus.pkl` (nine Wikipedia articles). |
| `condition4_frequency.py` | The missing fourth admissibility condition (frequency non-degeneracy) plus the `f_max` / `h_inf` measurement the paper's evaluation reports. |
| `concentration_simulation.py` | Small-field simulation backing the Cover-degeneracy lemma. Not needed to run the scheme; see *Why this file exists*. |

Reference papers (FBE, Invisible Encryption) are third-party works; cite them rather than redistributing their PDFs.

---

## Two different things are called "concentration"

The paper and the code both use the word, for **unrelated** results. Do not conflate them.

- **Anonymity-set concentration** (`lem:anonymity-concentration`; implementation notebook §6.4; `fig_concentration.png`). Nonempty anonymity sets `|Φ⁻¹(m)|` cluster at `S/p` with Chernoff tails. This is about the *seed space* and is what the feasibility threshold is built on.
- **Cover degeneracy** (`lem:cover-degeneracy`; `concentration_simulation.py`). If a cover is dominated by one repeated word, the induced-message distribution stops being balanced over `F_p`. This is about the *cover text* and is what admissibility condition 4 rules out.

The lemma labels were renamed to keep these apart. Older drafts called both "concentration".

---

## Admissibility: four conditions, of which the code ships three

A cover string `τ` is admissible when:

1. **Length.** `L ≥ max(κ, k+1)`.
2. **Distinctness.** At least `k` distinct words.
3. **Share separation.** At least `k` distinct nonzero values among `{H(w_i)}`.
4. **Frequency non-degeneracy.** `(k−1)·h_inf(τ) = ω(log λ)`, where `f_max(τ)` is the largest fraction of cover **positions** carrying a single share value and `h_inf(τ) = −log₂ f_max(τ)`.

`PhantomCrypt_implementation.ipynb` implements **all four**: `is_admissible(cover, k, p, freq_bits=128)` checks the frequency condition against an explicit bit target, and `freq_bits=None` restores the older three-condition behaviour for cells that only need 1--3 (the ED game is one; ED does not depend on condition 4).

`admissibility_check.ipynb` still implements **1--3 only**. Use `condition4_frequency.py` (drop-in `is_admissible_v2`) alongside it, or port the notebook's version across.

Conditions 1--3 alone are not enough. A cover made of one word repeated `L−k` times plus `k` distinct words passes all three while having `f_max ≈ 1`.

### What the measurement shows

On nine unmodified Wikipedia articles (~103,000 tokens), sliced into non-overlapping windows:

- **Conditions 1--3:** 100% pass at every window length `L ∈ {50,…,2000}`, in both threshold regimes. No authoring constraint.
- **Condition 4:** natural language is Zipfian and *does* concentrate. At `L = 2000` the dominant token (usually *the*) takes `f_max ≤ 9.1%` of positions, so `h_inf ≥ 3.5` bits (average 4.1). Worst case over all windows was `f_max = 24%` at `L = 50`.

Substituting into `(k−1)·h_inf` separates the two regimes sharply:

| Regime | Exponent | Verdict |
| --- | --- | --- |
| Growing `k = ⌈L/8⌉` | ≥31 bits at `L=100`, ≥863 bits at `L=2000` | satisfied by an enormous margin |
| Constant `k = 5` | 8--14 bits | does **not** close asymptotically |

Two cautions on the constant-`k` number. It bounds the bias rather than measuring it, and the simulation finds the true distance well below `f_max^(k−1)`, so condition 4 is sufficient rather than necessary. It is also not the binding constraint at constant parameters: the CD bound already fails to be negligible unless the seed margin grows (below).

---

## The seed margin is an *if and only if*

The CD bound is

```
eps_CD  <=  2*delta(lambda) + 2^(-(k-1)*h_inf(tau)) + eps_FBE(lambda)
```

with the seed drawn from `{0,1}^(lambda+s)`. This is negligible **if and only if** `s = omega(log lambda)`, condition 4 holds, and `eps_FBE` is itself negligible. It is *not* negligible for constant `s`, and only inverse-polynomial for `s = Theta(log lambda)`.

Nothing in the construction forces `s` to grow. A correct implementation can be run with constant `s` and no asymptotic guarantee at all, so this is a deployment choice, not something the code enforces. `s = lambda` (a `2*lambda`-bit seed) gives `delta <= 2^(-Omega(lambda))`.

---

## Requirements

Python 3.10+:

```bash
pip install numpy matplotlib pycryptodome kyber-py
```

`kyber-py` provides ML-KEM-768, `pycryptodome` provides AES-256-GCM. The notebook degrades gracefully if either is missing. `condition4_frequency.py` and `concentration_simulation.py` need only the standard library.

---

## Running things

**Implementation notebook.**

```bash
jupyter notebook PhantomCrypt_implementation.ipynb
```

Run top to bottom. Reproduces the evaluation figures and the wire-size table (baseline `1148 B`; two-payload `1400`--`1688 B`; single-payload fixed-bucket `1660 B`, constant in `ℓ`).

**Admissibility check.** Needs `corpus.pkl`, which is not bundled. Both files are notebooks, so run them in Jupyter rather than passing them to `python`:

```bash
jupyter nbconvert --execute --to notebook --inplace build_corpus.ipynb
jupyter nbconvert --execute --to notebook --inplace admissibility_check.ipynb
```

Both must run in the same directory. If you paste `build_corpus.ipynb` into a live kernel instead, its `argparse` call will read the kernel's launch arguments and exit; build the corpus inline instead:

```python
import urllib.request, urllib.parse, json, pickle, os
TITLES = ["Cryptography", "Quantum mechanics", "Climate change", "Roman Empire",
          "Photosynthesis", "Artificial intelligence", "World War II",
          "Albert Einstein", "History of the Internet"]
def fetch(title):
    params = {"action":"query","format":"json","prop":"extracts",
              "explaintext":"1","redirects":"1","titles":title}
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent":"phantomcrypt-corpus/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return next(iter(json.load(r)["query"]["pages"].values())).get("extract","")
pickle.dump({t: fetch(t) for t in TITLES}, open("corpus.pkl","wb"))
print("wrote corpus.pkl to", os.getcwd())
```

Avoid helper scripts that define `main()` in a shared kernel; several collide.

**Condition 4 and the simulation.**

```bash
python condition4_frequency.py      # demo: boilerplate fails, diverse text passes
python concentration_simulation.py  # several minutes; reproduces the lemma's shape
```

---

## Why `concentration_simulation.py` exists

It is a **verification artifact, not a dependency**. You do not need it to run, test, or deploy anything.

It exists because an earlier draft of the Cover-degeneracy lemma claimed the wrong mechanism: that the degenerate event inflates the anonymity set of the candidate message `m = v`. The simulation disproved that. Over `F_1009` at `k = 5`, `m = v` is in fact *under*-represented (ratio 0.097 against expectation); the real failure is that with every ordinate equal to `v` and `Σ L_j = 1`, the constant term collapses to `A = v(1 − L₀)` and the induced message

```
m(x0) = v + (s_new - v) * L0(x_new)^(-1)
```

becomes a function of `L₀` alone, whose pushforward is not uniform. The map loses one of its two randomness sources.

The paper cites this simulation's numbers directly (distance from uniform at the sampling-noise floor for `f_max = 0.005`, rising to 0.34 at `f_max = 0.975`, staying below `f_max^(k−1)` throughout), so it is kept here as the provenance for a published claim. Keep it if you want those numbers to be reproducible by a reader; it has no other role.

The small prime is not a shortcut. Buckets must be well populated for the empirical distribution to be meaningful, which needs `#seeds >> p`. At the real 256-bit prime the experiment is not runnable at all.

---

## Reproducibility notes

- **`corpus.pkl` is not in the repo.** The nine article titles are recorded (above), but Wikipedia articles change, so a fresh fetch reproduces the *phenomenon* and the *magnitudes* rather than exact window counts. Record your fetch date alongside results.
- Wire numbers assume a standard 96-bit (12-byte) AES-GCM nonce.
- Under GCM, `IV₁` and `IV₂` must be sampled independently, and the construction and the reference distribution must follow the identical nonce policy or the two distributions do not coincide.

---

## Known limitations and caveats

This is a **research prototype**, not audited or production-hardened software.

- **The asymptotic CD guarantee needs a growing seed margin.** See the *if and only if* above. The code does not enforce it.
- **Constant thresholds forfeit two things.** Small constant `k` gives up the open-world `(t,q)` guarantee and leaves condition 4 unclosed. The growing-threshold regime costs more (interpolation through `Θ(L)` points); that cost is measured in the notebook.
- **Threshold analysis assumes a near-uniform plausible message set.** Clean when payloads are high-entropy (keys, hashes, blobs). Genuinely low-entropy decoys split the analysis into two margins, marked as future work.
- **Conformance is not proven.** The paper defines what it would mean for the disclosed key set to be indistinguishable from an ordinary multi-record encrypted container, and states it as the principal open problem. This code does not produce a format-conformant container.
- **Stage-2 (device forensics) is out of scope for ED.** If PhantomCrypt software is found on a seized device, existence deniability no longer holds; only content deniability remains. Anamorphic encryption is strictly stronger on this axis.
- **CD hides designation, not content.** The coercer recovers `m*` among the `ℓ+1` openings. The scheme is meaningful only when `m*` is a plausible member of the decoy set.
- Plausibility is socio-technical: a cryptographically perfect decoy is worthless if the surrounding context makes it implausible.

---

## Security disclaimer

PhantomCrypt is provided for **research and evaluation only**. It has not been independently audited. Do not rely on it to protect anyone in a real coercion or high-risk situation. Deniable encryption can fail for reasons outside the cryptography (operational mistakes, device forensics, implausible decoys, legal regimes that punish suspected deniability). Use at your own risk.

---

## Citation

```bibtex
@misc{phantomcrypt,
  title  = {PhantomCrypt: Composing Existence and Content Deniability
            under a Post-Quantum Envelope},
  author = {XYZ et al.},
  year   = {2026},
  note   = {Under submission}
}
```



---

## License

LIT Secure and Correct Systems Lab, Johannes Kepler University Linz, Austria
