"""
demo_cli.py - Demo dự phòng KHÔNG cần trình duyệt.

  python demo_cli.py            # tạo file WAV + hình, phát âm trước/sau qua loa (Windows)
  python demo_cli.py --no-play  # chỉ tạo file

Kết quả:  output/*.wav  và  figures/*.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import echo_dsp as dsp
from diagrams import block_diagram

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
FIG = os.path.join(HERE, "figures")
plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})
C_IN, C_OUT, C_ACC = "#4C72B0", "#DD8452", "#C44E52"


def play(path):
    if sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME)


def save_wav(name, y, fs):
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(dsp.to_wav_bytes(dsp.normalize(y), fs))
    return path


def make_figures():
    """Các hình minh họa dùng cho slide thuyết trình."""
    alpha, D, N = 0.6, 8, 3

    # 1. Đáp ứng xung của 3 mô hình
    fig, axes = plt.subplots(1, 3, figsize=(12, 3), sharey=True)
    for ax, mode in zip(axes, dsp.MODES):
        h = dsp.impulse_response(mode, alpha, D, N, length=5 * D + 1)
        n = np.arange(len(h))
        ax.vlines(n, 0, h, color=C_IN)
        nz = np.abs(h) > 1e-12
        ax.plot(n[nz], h[nz], "o", color=C_IN, ms=4)
        ax.set_title(dsp.MODES[mode])
        ax.set_xlabel("n")
    axes[0].set_ylabel("h[n]")
    fig.suptitle(f"Đáp ứng xung (α = {alpha}, D = {D}, N = {N})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "impulse_responses.png"))
    plt.close(fig)

    # 2. Đáp ứng tần số FIR vs IIR (răng lược)
    w = np.linspace(0, np.pi, 2000)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    for mode, c in (("fir", C_IN), ("iir", C_OUT)):
        H = dsp.freq_response(mode, alpha, D, w)
        ax.plot(w / np.pi, 20 * np.log10(np.abs(H)), color=c, label=dsp.MODES[mode])
    ax.set_xlabel("ω / π")
    ax.set_ylabel("|H(e^jω)| (dB)")
    ax.set_title(f"Đáp ứng tần số dạng răng lược (α = {alpha}, D = {D})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "frequency_response.png"))
    plt.close(fig)

    # 3. Giản đồ cực - không FIR và IIR, cùng trường hợp không ổn định
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    th = np.linspace(0, 2 * np.pi, 400)
    cases = (("fir", alpha, "FIR: y[n]=x[n]+αx[n−D]"),
             ("iir", alpha, f"IIR ổn định (α = {alpha})"),
             ("iir", 1.1, "IIR KHÔNG ổn định (α = 1.1)"))
    for ax, (mode, a, title) in zip(axes, cases):
        zeros, poles = dsp.poles_zeros(mode, a, D)
        ax.plot(np.cos(th), np.sin(th), "k--", lw=0.8)
        nz_z, nz_p = zeros[np.abs(zeros) > 1e-9], poles[np.abs(poles) > 1e-9]
        ax.plot(nz_z.real, nz_z.imag, "o", mfc="none", mec=C_IN, ms=8, mew=1.5)
        ax.plot(nz_p.real, nz_p.imag, "x", color=C_ACC, ms=8, mew=1.5)
        origin = "x" if mode == "fir" else "o"
        ax.plot(0, 0, origin, color=C_ACC if mode == "fir" else C_IN, mfc="none", ms=8, mew=1.5)
        ax.annotate(f"bội {D}", (0, 0), (0.08, 0.1), fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)
        ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "pole_zero.png"))
    plt.close(fig)

    # 4. Sơ đồ khối của 3 mô hình
    for mode in dsp.MODES:
        fig = block_diagram(mode, N)
        fig.savefig(os.path.join(FIG, f"block_{mode}.png"), transparent=True)
        plt.close(fig)

    # 5. Dạng sóng trước/sau với tiếng vỗ tay
    fs = dsp.FS_DEFAULT
    x = dsp.make_clap(fs)
    xp, y, Dr = dsp.apply_echo(x, fs, 250, 0.6, "iir")
    t = np.arange(len(y)) / fs
    fig, axes = plt.subplots(2, 1, figsize=(10, 3.6), sharex=True)
    axes[0].plot(t, xp, color=C_IN, lw=0.6)
    axes[0].set_title("x[n]: tiếng vỗ tay gốc")
    axes[1].plot(t, y, color=C_OUT, lw=0.6)
    axes[1].set_title("y[n] = x[n] + 0.6·y[n−D],  τ = 250 ms")
    axes[1].set_xlabel("Thời gian (s)")
    axes[1].set_xlim(0, 2.2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "waveform_clap.png"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-play", action="store_true", help="không phát âm thanh")
    ap.add_argument("--delay", type=float, default=300, help="độ trễ tau (ms)")
    ap.add_argument("--alpha", type=float, default=0.6, help="hệ số suy giảm")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)

    print("== Kiểm chứng: echo_direct / echo_fast so với scipy.lfilter ==")
    for mode in dsp.MODES:
        r = dsp.verify(mode, args.alpha, 50)
        print(f"  {dsp.MODES[mode]:35s} sai số = {max(r['err_direct'], r['err_fast']):.1e}")

    fs = dsp.FS_DEFAULT
    for sample_name, maker in (("clap", dsp.make_clap), ("melody", dsp.make_melody)):
        x = maker(fs)
        orig = save_wav(f"{sample_name}_0_original.wav", x, fs)
        print(f"\n== Âm mẫu: {sample_name} ==")
        if not args.no_play:
            print("  ▶ Phát âm gốc")
            play(orig)
        for mode in dsp.MODES:
            xp, y, D = dsp.apply_echo(x, fs, args.delay, args.alpha, mode, N=3)
            path = save_wav(f"{sample_name}_{mode}.wav", y, fs)
            print(f"  {dsp.MODES[mode]:35s} D = {D} mẫu -> {os.path.relpath(path, HERE)}")
            if not args.no_play:
                play(path)

    make_figures()
    print(f"\nĐã lưu hình vào {os.path.relpath(FIG, HERE)}/ và âm thanh vào {os.path.relpath(OUT, HERE)}/")


if __name__ == "__main__":
    main()