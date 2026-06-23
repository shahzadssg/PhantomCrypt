# PhantomCrypt

A deniable-encryption scheme that combines **content deniability** and **existence deniability** under a **post-quantum** envelope. PhantomCrypt is research code accompanying the paper *PhantomCrypt*.

---

## What it does

PhantomCrypt protects a message against an adversary who can both **observe the channel** and later **coerce the user** into handing over keys. It targets two distinct properties at once:

- **Content deniability (CD)** -- via *False-Bottom Encryption (FBE)*. The true message `m*` and `ℓ` decoy messages are packed into a single container `c_FBE` with `ℓ+1` structurally **symmetric** keys. Given the container and all keys, an adversary cannot tell which opening was the intended one.
- **Existence deniability (ED)** -- via *Invisible Encryption (IE)*. A share `s_new` is derived from an **unmodified** cover text (Shamir-style interpolation with `m*` at `P(0)`), and `s_new` is uniform over the field, so it is indistinguishable from legitimate protocol randomness.
- **Post-quantum transport** -- both halves are wrapped in a hybrid **ML-KEM-768 + AES-256-GCM** envelope, producing a ciphertext `C = (C_kem, C₁, C₂, IV₁, IV₂)` that is object-indistinguishable from a standard reference distribution.

The honest recipient recovers `m*` using the pre-shared seed `x₀`; under coercion, any disclosed FBE key opens one of `ℓ+1` plausible plaintexts, with none marked as the true one. The field is `p = 2²⁵⁶ − 2³² − 977`.

---

## Repository layout

| File                                | What it is                                                                                                                                                        |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PhantomCrypt_implementation.ipynb` | Reference implementation + evaluation (construction, coverage/concentration, feasibility threshold, growing-`k` timings, wire sizes, byte-distribution detector). |
| `admissibility_check.ipynb`            | Standalone experiment: tests the cover-admissibility predicate on real text.                                                                                      |
| `build_corpus.ipynb`                   | Helper that builds `corpus.pkl` (the text corpus `admissibility_check.ipynb` reads).                                                                                 |

Reference papers (FBE, Invisible Encryption) are third-party works; cite them rather than redistributing their PDFs in a public repo unless their licenses permit it.

---

## Requirements

**Implementation / experiments (Python 3.10+):**

```bash
pip install numpy matplotlib pycryptodome kyber-py
```

`kyber-py` provides ML-KEM-768 and `pycryptodome` provides AES-256-GCM. The notebook degrades gracefully if either is missing (it prints which primitive is unavailable instead of running that cell).

---


## Run the implementation notebook

```bash
jupyter notebook PhantomCrypt_implementation.ipynb
```

Run the cells top to bottom. It validates the construction end to end and reproduces the evaluation figures and numbers in the paper, including the wire-size table (baseline `1148 B`; two-payload `1400`–`1688 B`; single-payload fixed-bucket `1660 B`, constant in `ℓ`).

---

## Run the admissibility check

This experiment shows that the admissibility predicate IE depends on is satisfied by real, unmodified prose (100% pass rate). It needs a corpus file, `corpus.pkl`, which is **not** bundled.

**From a terminal:**

```bash
python build_corpusipynb        # writes corpus.pkl (nine Wikipedia articles)
python admissibility_check.ipynb # prints the pass-rate table
```

Both must run from the same directory (so the script finds `corpus.pkl`).

**From Jupyter:** do not paste `build_corpus.ipynb` into a cell -- its `argparse` reads the kernel's launch arguments and exits with an error. Instead build the corpus inline (stdlib only):

```python
import urllib.request, urllib.parse, json, pickle, re, os
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
corpus = {t: fetch(t) for t in TITLES}
pickle.dump(corpus, open("corpus.pkl","wb"))
print("wrote corpus.pkl to", os.getcwd())
```

Then run the admissibility check **inline** (avoid scripts that define `main()`; both helper files define one and they collide in a shared kernel). The check requires only `hashlib`, `pickle`, `re`.

---

## Reproducibility notes

- **`corpus.pkl` is not in the repo.** The paper's exact nine articles are not recorded, so the literal window counts (e.g. "forty 2000-word windows") depend on the original corpus. A freshly built corpus reproduces the *phenomenon* (≈100% admissibility) but not the exact counts. If you have the original `corpus.pkl`, prefer it; otherwise record the article titles you use so the run is reproducible.
- The wire numbers assume a standard 96-bit (12-byte) AES-GCM nonce.

---

## Known limitations and caveats

This is a **research prototype**, not audited or production-hardened software.

- **Threshold analysis assumes a near-uniform plausible message set.** The feasibility-threshold results hold cleanly when plausible payloads are high-entropy (keys, hashes, coordinate blobs). For genuinely low-entropy decoys the analysis splits into two margins (field-size and entropy), which the paper marks as future work.
- **Stage-2 (device forensics) is out of scope for existence deniability.** If PhantomCrypt software is found on a seized device, existence deniability no longer holds; only content deniability remains.
- Plausibility is a socio-technical property: a cryptographically perfect decoy is worthless if the surrounding context makes it implausible. PhantomCrypt provides cryptographic symmetry among openings, not real-world plausibility of the decoy content.

---

## Security disclaimer

PhantomCrypt is provided for **research and evaluation only**. It has not been independently audited. Do not rely on it to protect anyone in a real coercion or high-risk situation. Deniable encryption can fail for reasons outside the cryptography (operational mistakes, device forensics, implausible decoys, legal regimes that punish suspected deniability). Use at your own risk.

---

## Citation

```bibtex
@misc{phantomcrypt,
  title  = {PhantomCrypt: ...},
  author = {...},
  year   = {2026},
  note   = {Under submission}
}
```

Replace with the published reference once available.

---

## License

No license is set yet. Until you add one, default copyright applies and others may not reuse the code. Add a `LICENSE` file (e.g. MIT or Apache-2.0 for the code) before publishing if you want it to be reusable.
