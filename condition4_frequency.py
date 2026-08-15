"""
PhantomCrypt: admissibility condition 4 (frequency non-degeneracy).

The published `is_admissible` checks only conditions 1-3 (length, distinctness,
share separation). Those three admit a cover that is 99% repetitions of one word,
which is exactly the case Lemma "Cover degeneracy" rules out. This module adds the
missing check and the measurement the paper's evaluation section reports.

Drop-in: paste into PhantomCrypt_implementation.ipynb after the cell defining
`is_admissible`, or import alongside admissibility_check.ipynb.
"""
from collections import Counter
from math import log2


def cover_fmax(cover, share_fn):
    """Largest fraction of cover POSITIONS carrying a single share value.

    Note this counts positions, not distinct words: repetition is the whole point,
    so `set(cover)` would discard exactly the information being measured.
    """
    counts = Counter(share_fn(w) for w in cover)
    return max(counts.values()) / len(cover)


def cover_hmin(cover, share_fn):
    """Share min-entropy h_inf(tau) = -log2 f_max, in bits per seed-driven selection."""
    return -log2(cover_fmax(cover, share_fn))


def frequency_non_degenerate(cover, k, share_fn, bits_required=None):
    """Condition 4: (k-1) * h_inf(tau) must be large.

    Asymptotically the paper requires (k-1)*h_inf = omega(log lambda). No finite
    cover can witness an asymptotic statement, so for a concrete check we compare
    against an explicit bit target; 128 is a sensible default for lambda=128.
    Returns (ok, exponent_bits, f_max).
    """
    if bits_required is None:
        bits_required = 128
    f_max = cover_fmax(cover, share_fn)
    exponent = (k - 1) * (-log2(f_max))
    return exponent >= bits_required, exponent, f_max


def is_admissible_v2(cover, k, p, share_fn, kappa=0, bits_required=None):
    """All four conditions. Same return shape as the notebook's is_admissible."""
    L = len(cover)
    if L < max(kappa, k + 1):
        return False, f"length L={L} < max(kappa={kappa}, k+1={k+1})"
    if len(set(cover)) < k:
        return False, f"only {len(set(cover))} distinct words < k={k} (distinctness)"
    nonzero = len({v for v in (share_fn(w) for w in set(cover)) if v != 0})
    if nonzero < k:
        return False, f"only {nonzero} distinct nonzero H(w) < k={k} (share separation)"
    ok, exponent, f_max = frequency_non_degenerate(cover, k, share_fn, bits_required)
    if not ok:
        return False, (f"f_max={f_max:.3f} gives (k-1)*h_inf={exponent:.1f} bits "
                       f"< {bits_required or 128} (frequency non-degeneracy)")
    return True, "admissible"


if __name__ == "__main__":
    import hashlib
    P = 2**256 - 2**32 - 977
    share = lambda w: int.from_bytes(hashlib.sha3_256(w.encode()).digest(), "big") % P

    # Passes conditions 1-3, fails condition 4: k distinct words plus heavy repetition.
    boilerplate = ["the"] * 1995 + [f"w{i}" for i in range(5)]
    diverse = [f"word{i%400}" for i in range(2000)]

    for name, cover in [("boilerplate", boilerplate), ("diverse", diverse)]:
        for k in (5, 250):
            ok, why = is_admissible_v2(cover, k, P, share)
            print(f"{name:12s} k={k:4d} -> {ok}  {why}")
