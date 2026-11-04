"""
app.py - Giao diện demo "Digital Echo Effect" (DGT302).

Chạy:  python -m streamlit run app.py      (hoặc nhấp đúp run_demo.bat)
"""
import inspect

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

import echo_dsp as dsp
from diagrams import block_diagram

st.set_page_config(page_title="Digital Echo Effect", page_icon="🔊", layout="wide")

C_IN, C_OUT, C_ACC = "#4C72B0", "#DD8452", "#C44E52"
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 9})


# ----------------------------------------------------------------------------
# Sidebar: tham số của hệ thống
# ----------------------------------------------------------------------------
st.sidebar.header("⚙️ Tham số hiệu ứng")
mode = st.sidebar.radio("Mô hình", list(dsp.MODES), format_func=dsp.MODES.get)
delay_ms = st.sidebar.slider("Độ trễ τ (ms)", 20, 1000, 300, step=10,
                             help="Thời gian giữa âm gốc và tiếng vọng. Tai người nghe tách được echo khi τ > ~50 ms.")
allow_unstable = mode == "iir" and st.sidebar.checkbox(
    "Cho phép |α| ≥ 1 (thử hệ KHÔNG ổn định)", value=False)
alpha = st.sidebar.slider("Hệ số suy giảm α", -1.1 if allow_unstable else -0.95,
                          1.1 if allow_unstable else 0.95, 0.6, step=0.05,
                          help="Biên độ tiếng vọng so với âm gốc. α < 0 đảo pha tiếng vọng.")
N = st.sidebar.slider("Số tiếng vọng N", 1, 8, 4) if mode == "fir_n" else 3

st.sidebar.divider()
if mode == "fir":
    st.sidebar.latex(r"y[n] = x[n] + \alpha\,x[n-D]")
    st.sidebar.latex(r"H(z) = 1 + \alpha z^{-D}")
elif mode == "fir_n":
    st.sidebar.latex(r"y[n] = \sum_{k=0}^{N} \alpha^k\, x[n-kD]")
    st.sidebar.latex(r"H(z) = \sum_{k=0}^{N} \alpha^k z^{-kD}")
else:
    st.sidebar.latex(r"y[n] = x[n] + \alpha\,y[n-D]")
    st.sidebar.latex(r"H(z) = \frac{1}{1 - \alpha z^{-D}}")
st.sidebar.caption("D = round(τ · Fs) là độ trễ tính bằng số mẫu.")

stable = dsp.is_stable(mode, alpha)
if not stable:
    st.sidebar.error(f"|α| = {abs(alpha):.2f} ≥ 1 → cực nằm ngoài/trên vòng tròn đơn vị → hệ KHÔNG ổn định BIBO!")


# ----------------------------------------------------------------------------
# Hàm vẽ
# ----------------------------------------------------------------------------
def plot_waveforms(x, y, fs, D):
    step = max(1, len(y) // 20000)  # rút gọn số điểm chỉ để vẽ cho nhanh
    t = np.arange(len(y)) / fs
    fig, axes = plt.subplots(2, 1, figsize=(10, 4.2), sharex=True)
    axes[0].plot(t[::step], x[::step], color=C_IN, lw=0.7)
    axes[0].set_title("Tín hiệu vào x[n]")
    axes[1].plot(t[::step], y[::step], color=C_OUT, lw=0.7)
    axes[1].set_title("Tín hiệu ra y[n] (có echo)")
    axes[1].set_xlabel("Thời gian (s)")
    # Đánh dấu vị trí các tiếng vọng sau điểm bắt đầu của âm gốc
    onset = np.argmax(np.abs(x) > 0.05 * np.max(np.abs(x)))
    n_marks = 1 if mode == "fir" else (N if mode == "fir_n" else 6)
    for k in range(1, n_marks + 1):
        tk = (onset + k * D) / fs
        if tk < t[-1]:
            axes[1].axvline(tk, color=C_ACC, ls="--", lw=0.8, alpha=0.6)
    fig.tight_layout()
    return fig


def plot_spectrum(x, y, fs, D):
    nfft = int(2 ** np.ceil(np.log2(len(y))))
    f = np.fft.rfftfreq(nfft, 1 / fs)
    X = 20 * np.log10(np.abs(np.fft.rfft(x, nfft)) + 1e-9)
    Y = 20 * np.log10(np.abs(np.fft.rfft(y, nfft)) + 1e-9)
    top = max(Y.max(), X.max()) + 5
    # Phóng to quanh tần số có năng lượng lớn nhất để thấy ~10 răng lược (cách nhau Fs/D)
    f0 = f[np.argmax(X)]
    span = 10 * fs / D
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
    for ax, (lo, hi), title in ((axes[0], (0, min(fs / 2, 4000)), "Toàn dải 0 – 4 kHz"),
                                (axes[1], (max(0, f0 - span / 2), f0 + span / 2),
                                 f"Phóng to: các răng lược cách nhau Fs/D = {fs / D:.2f} Hz")):
        ax.plot(f, X, color=C_IN, lw=0.8, label="|X(f)|")
        ax.plot(f, Y, color=C_OUT, lw=0.8, alpha=0.85, label="|Y(f)| = |H(f)|·|X(f)|")
        ax.set_xlim(lo, hi)
        ax.set_ylim(top - 70, top)
        ax.set_xlabel("Tần số (Hz)")
        ax.set_title(title)
    axes[0].set_ylabel("dB")
    axes[1].legend(loc="lower right", fontsize=7)
    fig.tight_layout()
    return fig


def plot_impulse(h, fs=None):
    n = np.arange(len(h))
    fig, ax = plt.subplots(figsize=(5, 3))
    nz = np.nonzero(np.abs(h) > 1e-12)[0]
    ax.vlines(n, 0, h, color=C_IN, lw=0.8)
    ax.plot(n[nz], h[nz], "o", color=C_IN, ms=4)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_title("Đáp ứng xung h[n]")
    ax.set_xlabel("n (mẫu)")
    fig.tight_layout()
    return fig


def plot_freq(H, w, title, xlabel="ω (rad/mẫu)", xscale=1.0):
    mag = np.abs(H)
    fig, axes = plt.subplots(2, 1, figsize=(5, 4.2), sharex=True)
    axes[0].plot(w * xscale, 20 * np.log10(mag + 1e-12), color=C_OUT)
    axes[0].set_ylabel("|H| (dB)")
    axes[0].set_title(title)
    axes[1].plot(w * xscale, np.angle(H), color=C_IN, lw=0.8)
    axes[1].set_ylabel("∠H (rad)")
    axes[1].set_xlabel(xlabel)
    fig.tight_layout()
    return fig


def plot_pz(zeros, poles):
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), "k--", lw=0.8, label="|z| = 1")
    if len(zeros):
        ax.plot(zeros.real, zeros.imag, "o", mfc="none", mec=C_IN, ms=8, mew=1.5, label="Không (zero)")
    if len(poles):
        ax.plot(poles.real, poles.imag, "x", color=C_ACC, ms=8, mew=1.5, label="Cực (pole)")
    # Đếm số cực/không tại gốc (bội)
    for pts, sym in ((zeros, "o"), (poles, "×")):
        k = int(np.sum(np.abs(pts) < 1e-9))
        if k > 1:
            ax.annotate(f"{sym} bội {k}", (0, 0), (0.08, 0.1), fontsize=8)
    lim = max(1.3, np.max(np.abs(np.concatenate([zeros, poles, [1]]))) * 1.15)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axhline(0, color="k", lw=0.4)
    ax.axvline(0, color="k", lw=0.4)
    ax.set_title("Giản đồ cực – không")
    ax.set_xlabel("Re{z}")
    ax.set_ylabel("Im{z}")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Giao diện chính
# ----------------------------------------------------------------------------
st.title("🔊 Digital Echo Effect")
st.caption("Đồ án môn Xử lý tín hiệu số (DGT302) – hiệu ứng tiếng vọng bằng hệ thống LTI rời rạc")

tab_demo, tab_sys, tab_check = st.tabs(["🎧 Demo âm thanh", "📐 Phân tích hệ thống", "✅ Kiểm chứng cài đặt"])

# ---------------------------- Tab 1: Demo âm thanh ----------------------------
with tab_demo:
    src = st.radio("Nguồn âm thanh", ["Âm thanh mẫu", "Ghi âm bằng micro", "Tải file WAV"], horizontal=True)
    fs, x = None, None
    if src == "Âm thanh mẫu":
        name = st.selectbox("Chọn âm mẫu", list(dsp.SAMPLES))
        fs, x = dsp.FS_DEFAULT, dsp.SAMPLES[name]()
    elif src == "Ghi âm bằng micro":
        rec = st.audio_input("Bấm nút micro, nói một câu ngắn (ví dụ: 'Xin chào thầy cô'), rồi bấm dừng")
        if rec is not None:
            fs, x = dsp.read_wav(rec.getvalue())
    else:
        up = st.file_uploader("Chọn file .wav (tối đa 15 giây được xử lý)", type=["wav"])
        if up is not None:
            try:
                fs, x = dsp.read_wav(up.getvalue())
            except Exception as exc:  # file WAV nén/không chuẩn
                st.error(f"Không đọc được file WAV này ({exc}). Hãy dùng WAV PCM 16-bit.")

    if x is None:
        st.info("Chọn hoặc ghi một âm thanh để bắt đầu.")
    else:
        xp, y, D = dsp.apply_echo(x, fs, delay_ms, alpha, mode, N)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tần số lấy mẫu Fs", f"{fs} Hz")
        m2.metric("Độ trễ D", f"{D} mẫu", f"τ = {D / fs * 1000:.0f} ms", delta_color="off", delta_arrow="off")
        m3.metric("Hệ số α", f"{alpha:.2f}")
        m4.metric("Biên độ đỉnh ra", f"{np.max(np.abs(y)):.2f}",
                  "đã chuẩn hóa khi phát" if np.max(np.abs(y)) > 0.95 else None,
                  delta_color="off", delta_arrow="off")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Âm gốc x[n]")
            st.audio(dsp.to_wav_bytes(xp, fs), format="audio/wav")
        with c2:
            st.subheader("Có echo y[n]")
            st.audio(dsp.to_wav_bytes(dsp.normalize(y), fs), format="audio/wav")
            st.download_button("⬇️ Tải file echo.wav", dsp.to_wav_bytes(dsp.normalize(y), fs),
                               file_name="echo.wav", mime="audio/wav")
        if not stable:
            st.error("Hệ không ổn định: biên độ tiếng vọng TĂNG theo thời gian (xem đồ thị bên dưới).")

        st.pyplot(plot_waveforms(xp, y, fs, D))
        st.caption("Các đường đứt đỏ đánh dấu thời điểm xuất hiện tiếng vọng: n₀ + kD.")
        with st.expander("Phổ tần số của tín hiệu vào/ra (FFT – Chương 7, 8)"):
            st.pyplot(plot_spectrum(xp, y, fs, D))
            st.markdown(f"Vì $Y(e^{{j\\omega}}) = H(e^{{j\\omega}})X(e^{{j\\omega}})$, phổ đầu ra bị nhân với "
                        f"đáp ứng răng lược của bộ lọc, có chu kỳ $F_s/D$ = **{fs / D:.2f} Hz**.")

# ------------------------- Tab 2: Phân tích hệ thống --------------------------
with tab_sys:
    st.markdown("**Sơ đồ khối của hệ thống** (bộ cộng, bộ nhân hệ số, phần tử trễ – Chương 2 & 9)")
    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        st.pyplot(block_diagram(mode, N))

    st.markdown("---")
    st.markdown("Để nhìn rõ đáp ứng xung và giản đồ cực–không, dùng **D nhỏ** (đơn vị: mẫu). "
                "Với âm thanh thật D rất lớn (hàng nghìn mẫu) nhưng hình dạng y hệt.")
    D_small = st.slider("D minh họa (mẫu)", 1, 16, 6)

    h = dsp.impulse_response(mode, alpha, D_small, N)
    w = np.linspace(0, np.pi, 2048)
    H = dsp.freq_response(mode, alpha, D_small, w, N)
    zeros, poles = dsp.poles_zeros(mode, alpha, D_small, N)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.pyplot(plot_impulse(h))
    with c2:
        fig = plot_freq(H, w / np.pi, f"Đáp ứng tần số (D = {D_small})", "ω / π")
        st.pyplot(fig)
    with c3:
        st.pyplot(plot_pz(zeros, poles))

    if mode == "iir":
        r = abs(alpha) ** (1 / D_small)
        if stable:
            st.success(f"D = {D_small} cực nằm trên đường tròn bán kính |α|^(1/D) = {r:.3f} < 1 "
                       "→ hệ nhân quả và **ổn định BIBO** (Chương 3).")
        else:
            st.error(f"Cực có bán kính |α|^(1/D) = {r:.3f} ≥ 1 → **không ổn định**: h[n] không tắt dần.")
        if stable:
            st.markdown(f"|H| dao động giữa 1/(1+|α|) = **{1 / (1 + abs(alpha)):.2f}** và "
                        f"1/(1−|α|) = **{1 / (1 - abs(alpha)):.2f}** → răng lược nhọn hơn bản FIR.")
    else:
        st.success("Hệ FIR: chỉ có cực tại z = 0 → **luôn ổn định**. "
                   f"Các zero nằm trên đường tròn bán kính |α|^(1/D) = {abs(alpha) ** (1 / D_small):.3f}.")
        if mode == "fir":
            st.markdown(f"|H| dao động giữa 1−|α| = **{1 - abs(alpha):.2f}** và 1+|α| = **{1 + abs(alpha):.2f}** "
                        "→ hình **răng lược (comb filter)** với D răng trên [0, 2π).")

    st.markdown("---")
    fs_real = dsp.FS_DEFAULT
    D_real = dsp.delay_samples(delay_ms, fs_real)
    st.markdown(f"**Đáp ứng tần số với độ trễ thực** τ = {delay_ms} ms, Fs = {fs_real} Hz → D = {D_real} mẫu. "
                f"Các răng lược cách nhau Fs/D = **{fs_real / D_real:.2f} Hz** (phóng to đoạn đầu trục tần số).")
    f_max = min(fs_real / 2, 8 * fs_real / D_real)
    f = np.linspace(0, f_max, 4000)
    Hr = dsp.freq_response(mode, alpha, D_real, 2 * np.pi * f / fs_real, N)
    fig, ax = plt.subplots(figsize=(10, 2.6))
    ax.plot(f, 20 * np.log10(np.abs(Hr) + 1e-12), color=C_OUT)
    ax.set_xlabel("Tần số (Hz)")
    ax.set_ylabel("|H| (dB)")
    fig.tight_layout()
    st.pyplot(fig)

# ------------------------- Tab 3: Kiểm chứng cài đặt --------------------------
with tab_check:
    st.markdown("Hệ thống được cài đặt bằng **3 cách độc lập**, kết quả phải trùng nhau:")
    st.markdown("1. `echo_direct` – tính từng mẫu với **bộ đệm vòng** (delay line), giống chạy thời gian thực trên chip DSP.\n"
                "2. `echo_fast` – tính theo khối bằng numpy (dùng cho demo âm thanh).\n"
                "3. `scipy.signal.lfilter(b, a, x)` – hàm lọc chuẩn, dùng làm tham chiếu.")
    D_chk = st.number_input("D để kiểm tra (mẫu)", 1, 2000, 50)
    if st.button("▶️ Chạy kiểm chứng trên 4000 mẫu nhiễu ngẫu nhiên"):
        r = dsp.verify(mode, alpha, int(D_chk), N)
        st.table({
            "Cách cài đặt": ["echo_direct (từng mẫu)", "echo_fast (theo khối)", "scipy lfilter (tham chiếu)"],
            "Sai số lớn nhất so với lfilter": [f"{r['err_direct']:.2e}", f"{r['err_fast']:.2e}", "0"],
            "Thời gian (ms)": [f"{r['t_direct'] * 1e3:.2f}", f"{r['t_fast'] * 1e3:.2f}", f"{r['t_lfilter'] * 1e3:.2f}"],
        })
        if max(r["err_direct"], r["err_fast"]) < 1e-9:
            st.success("Ba cách cài đặt cho cùng kết quả (sai số chỉ ở mức làm tròn số thực ~1e-16).")
    with st.expander("Xem mã nguồn echo_direct (phương trình sai phân + bộ đệm vòng)"):
        st.code(inspect.getsource(dsp.echo_direct), language="python")
    with st.expander("Xem mã nguồn echo_fast"):
        st.code(inspect.getsource(dsp.echo_fast), language="python")