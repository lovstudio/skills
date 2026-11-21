"""Binary line art -> one closed path -> Fourier epicycle terms.

Two decompositions are supported:
  xy       two real series, x(t) = sum a_k cos kt + b_k sin kt and y(t) likewise; drawn as two
           epicycle chains whose tips are projected onto the pen (the layout of Coding Train #130.1).
  complex  one complex series z(t) = sum c_k e^{ikt}; one chain whose tip is the pen (3Blue1Brown style).
"""
import sys
from dataclasses import dataclass

import cv2
import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial import cKDTree


def order_contours(ink: np.ndarray, min_len: int = 16) -> np.ndarray:
    """Chain every ink-blob boundary into one closed path (complex, image coords, y down).

    Contours are joined along a minimum spanning tree of their closest-point distances and
    toured depth-first: each connector is walked out and back on the same segment, so the
    unavoidable "pen-down" jumps stay short and read as single thin strokes instead of long
    diagonals across the face (which a greedy nearest-neighbour order produces).
    """
    contours, _ = cv2.findContours(ink, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    loops = [c[:, 0, :].astype(np.float64) for c in contours if len(c) >= min_len]
    if not loops:
        raise SystemExit("line art has no usable contours; lower --min-area or check the photo")
    k = len(loops)
    dist = np.zeros((k, k))
    link = {}  # (i, j) -> (index on loop i, index on loop j) of their closest pair
    trees = [cKDTree(l) for l in loops]
    for i in range(k):
        for j in range(i + 1, k):
            d, idx = trees[i].query(loops[j])
            b = int(d.argmin())
            dist[i, j] = dist[j, i] = d[b] + 1e-6  # csgraph treats 0 as "no edge"
            link[(i, j)], link[(j, i)] = (int(idx[b]), b), (b, int(idx[b]))
    mst = minimum_spanning_tree(dist).toarray()
    adj = [[] for _ in range(k)]
    for i, j in zip(*np.nonzero(mst)):
        adj[i].append(j)
        adj[j].append(i)

    out = []
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * k + 100))

    def tour(i, entry, parent):
        loop, n = loops[i], len(loops[i])
        at = {}
        for c in adj[i]:
            if c != parent:
                at.setdefault(link[(i, c)][0], []).append(c)
        for s in range(n + 1):
            p = loop[(entry + s) % n]
            out.append(p)
            if s < n:
                for c in at.get((entry + s) % n, []):
                    tour(c, link[(i, c)][1], i)
                    out.append(p)  # walk the connector back to where we left this loop

    root = min(range(k), key=lambda i: loops[i][:, 1].min())  # start at the top of the head
    tour(root, int(loops[root][:, 1].argmin()), -1)
    path = np.asarray(out)
    return path[:, 0] + 1j * path[:, 1]


def resample(z: np.ndarray, m: int) -> np.ndarray:
    """Uniform arc-length resampling of a closed path to m points."""
    closed = np.append(z, z[0])
    seg = np.abs(np.diff(closed))
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], m, endpoint=False)
    return np.interp(u, s, closed.real) + 1j * np.interp(u, s, closed.imag)


@dataclass
class Terms:
    freq: np.ndarray    # integer frequency k (signed in complex mode)
    amp: np.ndarray     # radius r_k
    phase: np.ndarray   # phase phi_k


@dataclass
class Spectrum:
    mode: str
    m: int
    center: complex
    terms: list  # [Terms] for complex, [Terms_x, Terms_y] for xy


def _real_terms(sig):
    m = len(sig)
    X = np.fft.rfft(sig) / m
    k = np.arange(1, len(X) - (m % 2 == 0))  # drop DC and the Nyquist bin
    amp, phase = 2 * np.abs(X[k]), np.angle(X[k])
    order = np.argsort(-amp)
    return Terms(k[order], amp[order], phase[order])


def spectrum(z: np.ndarray, mode: str) -> Spectrum:
    m, center = len(z), z.mean()
    if mode == "xy":
        return Spectrum(mode, m, center, [_real_terms(z.real), _real_terms(z.imag)])
    C = np.fft.fft(z - center) / m
    k = np.fft.fftfreq(m, 1 / m).astype(int)
    nz = k != 0
    k, C = k[nz], C[nz]
    order = np.argsort(-np.abs(C))
    return Spectrum(mode, m, center, [Terms(k[order], np.abs(C[order]), np.angle(C[order]))])


def reconstruct(sp: Spectrum, n: int, t: np.ndarray) -> np.ndarray:
    """Path evaluated at parameter values t (radians) using the n largest terms per series."""
    def real_series(T):
        return (T.amp[:n, None] * np.cos(np.outer(T.freq[:n], t) + T.phase[:n, None])).sum(0)
    if sp.mode == "xy":
        tx, ty = sp.terms
        return sp.center + real_series(tx) + 1j * real_series(ty)
    T = sp.terms[0]
    return sp.center + (T.amp[:n, None] * np.exp(1j * (np.outer(T.freq[:n], t) + T.phase[:n, None]))).sum(0)


def relative_error(z: np.ndarray, zn: np.ndarray) -> float:
    return float(np.linalg.norm(zn - z) / np.linalg.norm(z - z.mean()))


def decay_exponent(sp: Spectrum, kmax: int = 512) -> float:
    """Fit r_k ~ k^-p on the amplitude per harmonic k (both series pooled)."""
    amp = np.zeros(kmax + 1)
    for T in sp.terms:
        sel = (np.abs(T.freq) >= 1) & (np.abs(T.freq) <= kmax)
        np.add.at(amp, np.abs(T.freq[sel]), T.amp[sel] ** 2)
    k = np.arange(1, kmax + 1)
    r = np.sqrt(amp[1:])
    ok = r > 0
    p, _ = np.polyfit(np.log(k[ok]), np.log(r[ok]), 1)
    return float(-p)
