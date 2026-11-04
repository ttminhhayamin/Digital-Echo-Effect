"""
diagrams.py - Vẽ sơ đồ khối (bộ cộng, bộ nhân, phần tử trễ z^-D) bằng matplotlib.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

BLUE, ORANGE, GREY = "#4C72B0", "#DD8452", "#444444"


def _box(ax, x, y, text, w=1.1, h=0.6):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02",
                                fc="#eef2fa", ec=BLUE, lw=1.4))
    ax.text(x, y, text, ha="center", va="center", fontsize=11)


def _adder(ax, x, y, r=0.25):
    ax.add_patch(Circle((x, y), r, fc="#fde7da", ec=ORANGE, lw=1.4))
    ax.text(x, y, "+", ha="center", va="center", fontsize=13, fontweight="bold")


def _arrow(ax, p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.3, shrinkA=0, shrinkB=0))


def _line(ax, pts):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=GREY, lw=1.3)


def _dot(ax, x, y):
    ax.plot(x, y, "o", color=GREY, ms=4)


def block_diagram(mode, N=3, figsize=(8, 2.6)):
    fig, ax = plt.subplots(figsize=figsize)
    r = 0.25
    if mode == "fir":
        # x[n] ──●────────────(+)──> y[n]
        #        └─ z^-D ─ ×α ──┘
        _line(ax, [(0.6, 0), (1.5, 0)]); _dot(ax, 1.5, 0)
        _arrow(ax, (1.5, 0), (5 - r, 0)); _adder(ax, 5, 0); _arrow(ax, (5 + r, 0), (6.6, 0))
        _line(ax, [(1.5, 0), (1.5, -1.3)]); _arrow(ax, (1.5, -1.3), (2.45, -1.3))
        _box(ax, 3.0, -1.3, "$z^{-D}$"); _arrow(ax, (3.55, -1.3), (4.05, -1.3))
        _box(ax, 4.5, -1.3, r"$\times\,\alpha$", w=0.9)
        _line(ax, [(4.95, -1.3), (5, -1.3)]); _arrow(ax, (5, -1.3), (5, -r))
        ax.text(3.7, -0.75, "nhánh thuận (feed-forward)", fontsize=8, color=BLUE, ha="center")
        ax.text(0.5, 0, "$x[n]$", ha="right", va="center", fontsize=12)
        ax.text(6.7, 0, "$y[n]$", ha="left", va="center", fontsize=12)
        ax.set_xlim(-0.3, 7.6); ax.set_ylim(-1.9, 0.6)
    elif mode == "iir":
        # x[n] ──(+)──────●──> y[n]
        #         └─ ×α ─ z^-D ─┘
        _arrow(ax, (0.6, 0), (2 - r, 0)); _adder(ax, 2, 0)
        _line(ax, [(2 + r, 0), (5, 0)]); _dot(ax, 5, 0); _arrow(ax, (5, 0), (6.6, 0))
        _line(ax, [(5, 0), (5, -1.3)]); _arrow(ax, (5, -1.3), (4.65, -1.3))
        _box(ax, 4.1, -1.3, "$z^{-D}$"); _arrow(ax, (3.55, -1.3), (3.2, -1.3))
        _box(ax, 2.75, -1.3, r"$\times\,\alpha$", w=0.9)
        _line(ax, [(2.3, -1.3), (2, -1.3)]); _arrow(ax, (2, -1.3), (2, -r))
        ax.text(3.5, -0.75, "vòng phản hồi (feedback)", fontsize=8, color=ORANGE, ha="center")
        ax.text(0.5, 0, "$x[n]$", ha="right", va="center", fontsize=12)
        ax.text(6.7, 0, "$y[n]$", ha="left", va="center", fontsize=12)
        ax.set_xlim(-0.3, 7.6); ax.set_ylim(-1.9, 0.6)
    else:
        # Dạng trực tiếp FIR (transversal): chuỗi trễ ở trên, các nhánh nhân, dãy bộ cộng ở dưới
        K = min(N, 4)
        dx = 1.8
        _line(ax, [(0.6, 0), (1.2, 0)])
        for k in range(K + 1):
            xk = 1.2 + k * dx
            _dot(ax, xk, 0)
            if k < K:
                _arrow(ax, (xk, 0), (xk + dx / 2 - 0.55, 0))
                _box(ax, xk + dx / 2, 0, "$z^{-D}$")
                _line(ax, [(xk + dx / 2 + 0.55, 0), (xk + dx, 0)])
            _arrow(ax, (xk, 0), (xk, -0.95))
            label = {0: r"$\times 1$", 1: r"$\times\,\alpha$"}.get(k, rf"$\times\,\alpha^{k}$")
            _box(ax, xk, -1.25, label, w=0.9)
            if k == 0:
                _line(ax, [(xk, -1.55), (xk, -2.4)])
                _line(ax, [(xk, -2.4), (xk + dx - r, -2.4)])
            else:
                _adder(ax, xk, -2.4)
                _arrow(ax, (xk, -1.55), (xk, -2.4 + r))
                if k < K:
                    _arrow(ax, (xk + r, -2.4), (xk + dx - r, -2.4))
        xe = 1.2 + K * dx
        if N > K:
            ax.text(xe + 0.6, -1.25, f"… đến $\\alpha^{{{N}}}$", fontsize=10, va="center")
        _arrow(ax, (xe + r, -2.4), (xe + 1.2, -2.4))
        ax.text(0.5, 0, "$x[n]$", ha="right", va="center", fontsize=12)
        ax.text(xe + 1.3, -2.4, "$y[n]$", ha="left", va="center", fontsize=12)
        ax.set_xlim(-0.3, xe + 2.2); ax.set_ylim(-2.9, 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig