"""
echo_dsp.py - Lõi xử lý tín hiệu cho đề tài "Digital Echo Effect" (DGT302).

Hiệu ứng tiếng vọng (echo) được mô hình hóa bằng 3 hệ thống LTI rời rạc:

  1. "fir"   - Một tiếng vọng (FIR comb filter)
        y[n] = x[n] + a*x[n-D]                 H(z) = 1 + a*z^-D
  2. "fir_n" - N tiếng vọng, tắt dần (FIR)
        y[n] = sum_{k=0..N} a^k * x[n-kD]      H(z) = sum_{k=0..N} a^k * z^-kD
  3. "iir"   - Tiếng vọng lặp vô hạn (IIR feedback comb filter)
        y[n] = x[n] + a*y[n-D]                 H(z) = 1 / (1 - a*z^-D)

  D = round(tau * Fs) là độ trễ tính bằng mẫu, a (alpha) là hệ số suy giảm.
"""
import io
import time

import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter

MODES = {
    "fir": "1 tiếng vọng (FIR)",
    "fir_n": "N tiếng vọng (FIR)",
    "iir": "Vọng lặp vô hạn - feedback (IIR)",
}


# ----------------------------------------------------------------------------
# Tham số
# ----------------------------------------------------------------------------
def delay_samples(delay_ms, fs):
    """Đổi độ trễ tau (ms) sang số mẫu D = round(tau * Fs)."""
    return max(1, int(round(delay_ms * 1e-3 * fs)))


def coefficients(mode, alpha, D, N=3):
    """Hệ số tử b và mẫu a của H(z) = B(z)/A(z) (dạng dùng cho scipy lfilter)."""
    if mode == "fir":
        b = np.zeros(D + 1)
        b[0], b[D] = 1.0, alpha
        a = np.array([1.0])
    elif mode == "fir_n":
        b = np.zeros(N * D + 1)
        b[::D] = alpha ** np.arange(N + 1)
        a = np.array([1.0])
    elif mode == "iir":
        b = np.array([1.0])
        a = np.zeros(D + 1)
        a[0], a[D] = 1.0, -alpha
    else:
        raise ValueError(f"mode không hợp lệ: {mode}")
    return b, a


def tail_length(mode, alpha, D, N=3, fs=None, max_seconds=8.0):
    """Số mẫu cần thêm vào cuối để nghe hết tiếng vọng.

    IIR: cắt khi a^k nhỏ hơn -60 dB (a^k < 1e-3), tối đa max_seconds.
    """
    if mode == "fir":
        return D
    if mode == "fir_n":
        return N * D
    if abs(alpha) < 1e-6:
        return D
    if abs(alpha) >= 1:
        k = 30  # hệ không ổn định: chỉ lấy 30 lần lặp để thấy biên độ tăng
    else:
        k = int(np.ceil(np.log(1e-3) / np.log(abs(alpha))))
    L = k * D
    if fs is not None:
        L = min(L, int(max_seconds * fs))
    return L


# ----------------------------------------------------------------------------
# Cài đặt 1: trực tiếp từng mẫu với bộ đệm vòng (giống chạy trên chip DSP)
# ----------------------------------------------------------------------------
def echo_direct(x, alpha, D, mode="fir", N=3):
    """Tính phương trình sai phân từng mẫu một, dùng delay line dạng circular buffer.

    Đây là cách hiệu ứng echo chạy thời gian thực trên vi xử lý DSP (Chương 9):
    mỗi mẫu vào chỉ cần vài phép nhân-cộng và một bộ nhớ D (hoặc N*D) mẫu.
    Chậm trong Python, dùng để kiểm chứng và giải thích.
    """
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)

    if mode == "iir":
        buf = np.zeros(D)  # lưu D mẫu RA gần nhất: y[n-1] ... y[n-D]
        idx = 0
        for n in range(len(x)):
            yn = x[n] + alpha * buf[idx]  # buf[idx] đang chứa y[n-D]
            buf[idx] = yn
            idx = (idx + 1) % D
            y[n] = yn
        return y

    taps = 1 if mode == "fir" else N
    L = taps * D
    buf = np.zeros(L)  # lưu L mẫu VÀO gần nhất: x[n-1] ... x[n-L]
    idx = 0
    for n in range(len(x)):
        acc = x[n]
        for k in range(1, taps + 1):
            acc += alpha ** k * buf[(idx - k * D) % L]  # x[n-kD]
        buf[idx] = x[n]
        idx = (idx + 1) % L
        y[n] = acc
    return y


# ----------------------------------------------------------------------------
# Cài đặt 2: vector hóa bằng numpy (nhanh, dùng cho âm thanh thật)
# ----------------------------------------------------------------------------
def echo_fast(x, alpha, D, mode="fir", N=3):
    """Kết quả giống hệt echo_direct nhưng tính theo khối.

    FIR: cộng bản sao trễ của x.
    IIR: vì phản hồi trễ đúng D mẫu, khối mẫu [mD, (m+1)D) chỉ phụ thuộc
         khối ngay trước nó => tính lần lượt từng khối D mẫu.
    """
    x = np.asarray(x, dtype=float)
    y = x.copy()

    if mode == "iir":
        for start in range(D, len(x), D):
            stop = min(start + D, len(x))
            y[start:stop] += alpha * y[start - D:stop - D]
        return y

    taps = 1 if mode == "fir" else N
    for k in range(1, taps + 1):
        if k * D >= len(x):
            break
        y[k * D:] += alpha ** k * x[:-k * D]
    return y


def apply_echo(x, fs, delay_ms, alpha, mode="fir", N=3):
    """Áp hiệu ứng echo lên tín hiệu âm thanh (thêm đuôi để nghe hết tiếng vọng)."""
    D = delay_samples(delay_ms, fs)
    pad = tail_length(mode, alpha, D, N, fs)
    xp = np.concatenate([np.asarray(x, dtype=float), np.zeros(pad)])
    return xp, echo_fast(xp, alpha, D, mode, N), D


# ----------------------------------------------------------------------------
# Phân tích: đáp ứng xung, đáp ứng tần số, cực - không
# ----------------------------------------------------------------------------
def impulse_response(mode, alpha, D, N=3, length=None):
    """h[n] = đáp ứng của hệ với x[n] = delta[n]."""
    if length is None:
        length = 6 * D + 1 if mode == "iir" else tail_length(mode, alpha, D, N) + D + 1
    delta = np.zeros(length)
    delta[0] = 1.0
    return echo_fast(delta, alpha, D, mode, N)


def freq_response(mode, alpha, D, w, N=3):
    """H(e^jw) theo công thức đóng (không phụ thuộc D lớn hay nhỏ)."""
    zD = np.exp(-1j * w * D)  # z^-D trên vòng tròn đơn vị
    if mode == "fir":
        return 1 + alpha * zD
    if mode == "fir_n":
        return sum(alpha ** k * zD ** k for k in range(N + 1))
    return 1 / (1 - alpha * zD)


def poles_zeros(mode, alpha, D, N=3):
    """Trả về (zeros, poles) trên mặt phẳng z."""
    b, a = coefficients(mode, alpha, D, N)
    b = np.trim_zeros(b, "b")
    zeros = np.roots(b) if len(b) > 1 else np.array([])
    poles = np.roots(a) if len(a) > 1 else np.array([])
    # Bù cực/không tại gốc tọa độ do bậc tử và mẫu khác nhau
    diff = (len(b) - 1) - (len(a) - 1)
    if diff > 0:
        poles = np.concatenate([poles, np.zeros(diff)])
    elif diff < 0:
        zeros = np.concatenate([zeros, np.zeros(-diff)])
    return zeros, poles


def is_stable(mode, alpha):
    """FIR luôn ổn định; IIR ổn định BIBO khi mọi cực |p| = |a|^(1/D) < 1  <=>  |a| < 1."""
    return mode != "iir" or abs(alpha) < 1


# ----------------------------------------------------------------------------
# Kiểm chứng: 3 cách cài đặt phải cho cùng một kết quả
# ----------------------------------------------------------------------------
def verify(mode, alpha, D, N=3, length=4000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(length)
    b, a = coefficients(mode, alpha, D, N)

    t0 = time.perf_counter(); y_direct = echo_direct(x, alpha, D, mode, N); t1 = time.perf_counter()
    y_fast = echo_fast(x, alpha, D, mode, N); t2 = time.perf_counter()
    y_ref = lfilter(b, a, x); t3 = time.perf_counter()

    return {
        "err_direct": float(np.max(np.abs(y_direct - y_ref))),
        "err_fast": float(np.max(np.abs(y_fast - y_ref))),
        "t_direct": t1 - t0,
        "t_fast": t2 - t1,
        "t_lfilter": t3 - t2,
    }


# ----------------------------------------------------------------------------
# Tín hiệu mẫu có sẵn (không cần file)
# ----------------------------------------------------------------------------
FS_DEFAULT = 22050


def make_clap(fs=FS_DEFAULT, duration=1.5):
    """Tiếng vỗ tay: nhiễu trắng tắt dần nhanh (~20 ms). Nghe echo rõ nhất."""
    rng = np.random.default_rng(1)
    n = np.arange(int(0.12 * fs))
    burst = rng.standard_normal(len(n)) * np.exp(-n / (0.02 * fs))
    x = np.zeros(int(duration * fs))
    start = int(0.05 * fs)
    x[start:start + len(burst)] = burst
    return 0.8 * x / np.max(np.abs(x))


def make_beep(fs=FS_DEFAULT, duration=1.5, f0=880.0):
    """Tiếng 'bíp' hình sin dài 80 ms."""
    n = np.arange(int(0.08 * fs))
    tone = np.sin(2 * np.pi * f0 * n / fs) * np.hanning(len(n))
    x = np.zeros(int(duration * fs))
    start = int(0.05 * fs)
    x[start:start + len(tone)] = tone
    return 0.8 * x


def make_melody(fs=FS_DEFAULT):
    """Giai điệu Đô - Mi - Son - Đô (âm sắc giống đàn: các họa âm tắt dần)."""
    notes = [261.63, 329.63, 392.00, 523.25]
    note_len = int(0.35 * fs)
    n = np.arange(note_len)
    env = np.exp(-n / (0.12 * fs))
    out = []
    for f in notes:
        tone = sum((0.6 ** h) * np.sin(2 * np.pi * f * (h + 1) * n / fs) for h in range(4))
        out.append(tone * env)
    x = np.concatenate(out + [np.zeros(int(0.6 * fs))])
    return 0.8 * x / np.max(np.abs(x))


SAMPLES = {
    "Tiếng vỗ tay (clap)": make_clap,
    "Tiếng bíp (sin 880 Hz)": make_beep,
    "Giai điệu Đô-Mi-Son-Đô": make_melody,
}


# ----------------------------------------------------------------------------
# Đọc / ghi WAV
# ----------------------------------------------------------------------------
def read_wav(data, max_seconds=15.0):
    """Đọc WAV (đường dẫn hoặc bytes) -> (fs, tín hiệu mono float trong [-1, 1])."""
    if isinstance(data, (bytes, bytearray)):
        data = io.BytesIO(data)
    fs, x = wavfile.read(data)
    if x.dtype == np.int16:
        x = x / 32768.0
    elif x.dtype == np.int32:
        x = x / 2147483648.0
    elif x.dtype == np.uint8:
        x = (x.astype(float) - 128) / 128.0
    x = np.asarray(x, dtype=float)
    if x.ndim > 1:
        x = x.mean(axis=1)  # stereo -> mono
    return fs, x[: int(max_seconds * fs)]


def normalize(y, peak=0.95):
    """Chuẩn hóa biên độ để tránh vỡ tiếng (clipping) khi phát."""
    m = np.max(np.abs(y))
    return y * (peak / m) if m > peak else y


def to_wav_bytes(y, fs):
    """Tín hiệu float -> bytes WAV 16-bit PCM."""
    y16 = np.int16(np.clip(y, -1, 1) * 32767)
    buf = io.BytesIO()
    wavfile.write(buf, fs, y16)
    return buf.getvalue()