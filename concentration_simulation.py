"""
PhantomCrypt: cover-degeneracy simulation (Lemma "Cover degeneracy").

VERIFICATION ARTIFACT. Not needed to run, test, or deploy the scheme. It exists
because it disproved an earlier version of the lemma, and because the paper now
cites its numbers.

What it measures
----------------
For a fixed transcript s_new, it enumerates seeds, derives abscissae by hash
chaining (x_j = H(x_{j-1})) and ordinates by PRNG word selection (s_j = H(w_ij)),
interpolates, inverts, and histograms the induced candidate message m(x0). It then
reports the statistical distance of that histogram from uniform over F_p, sweeping
f_max (how repetition-heavy the cover is) and the threshold k.

What it found
-------------
Repetition does break the balance, so admissibility condition 4 is justified. But
NOT by the mechanism first claimed: the candidate m = v is under-represented, not
inflated. On the degenerate event every ordinate equals v, and since sum_j L_j = 1
the constant term collapses to A = v(1 - L0), leaving

    m(x0) = v + (s_new - v) * L0(x_new)^(-1)

a function of L0 alone, with non-uniform pushforward. The failure is the loss of
one of two independent randomness sources.

The measured distance stays BELOW the f_max^(k-1) bound everywhere it is
resolvable, so condition 4 is sufficient rather than necessary.

Why p = 1009
------------
Buckets must be well populated for the empirical distribution to mean anything,
which needs #seeds >> p. At the real 256-bit prime the experiment is not runnable.
The small field is a requirement of the measurement, not a shortcut.

Runtime: several minutes. Output feeds the table quoted in the paper's
cover-degeneracy remark.
"""
import hashlib, random
from collections import Counter
p=1009
def H(x): return int.from_bytes(hashlib.sha3_256(str(x).encode()).digest(),'big')%p

def induced(cover,t,n=300000,s_new=123):
    Hw=[H(w) for w in cover]; L=len(cover); c=Counter()
    for x0 in range(n):
        xs,cur,g=[],x0,0
        while len(xs)<t-1 and g<400:
            cur=H(cur); g+=1
            if cur!=0 and cur not in xs: xs.append(cur)
        if len(xs)<t-1: continue
        xnew,g=cur,0
        while (xnew in xs or xnew==0) and g<400: xnew=H(xnew); g+=1
        rng=random.Random(x0); sj=[Hw[rng.randrange(L)] for _ in range(t-1)]
        nodes=[0]+xs
        def Lk(k):
            nu=de=1
            for j,xj in enumerate(nodes):
                if j==k: continue
                nu=nu*(xnew-xj)%p; de=de*(nodes[k]-xj)%p
            return nu*pow(de,p-2,p)%p
        B=Lk(0)
        if B==0: continue
        A=sum(sj[j-1]*Lk(j) for j in range(1,t))%p
        c[(s_new-A)*pow(B,p-2,p)%p]+=1
    return c

def sd(c):
    tot=sum(c.values())
    return 0.5*sum(abs(c.get(m,0)/tot-1/p) for m in range(p))

print(f"{'f_max':>8} {'t':>3} {'stat.dist':>10} {'f_max^(t-1)':>12}")
for fm_target,ndom in [(0.005,1),(0.25,50),(0.50,100),(0.75,150),(0.90,180),(0.975,195)]:
    cover=["the"]*ndom+[f"w{i}" for i in range(200-ndom)]
    fm=ndom/200 if ndom>1 else 1/200
    for t in (5,9):
        d=sd(induced(cover,t))
        print(f"{fm:8.3f} {t:3d} {d:10.4f} {fm**(t-1):12.5f}")
