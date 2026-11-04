# 🔊 Digital Echo Effect

> Tạo hiệu ứng tiếng vọng (echo) bằng hệ thống LTI rời rạc, kèm ứng dụng demo tương tác trên trình duyệt.

Đồ án môn **Xử lý tín hiệu số (DGT302)**. Dự án mô hình hóa tiếng vọng bằng ba bộ lọc FIR/IIR,
cho phép nghe trực tiếp kết quả và phân tích hệ thống trong miền thời gian, miền z và miền tần số.

> **Dạng sóng tiếng vỗ tay sau khi qua bộ lọc echo IIR** — Hình được tạo bằng `python demo_cli.py --no-play` (lưu tại `figures/waveform_clap.png`).

## ✨ Tính năng

- **3 mô hình echo:** một tiếng vọng (FIR), N tiếng vọng (FIR) và vọng lặp vô hạn (IIR).
- **Nghe thử ngay:** âm mẫu có sẵn, ghi âm trực tiếp bằng micro hoặc tải file WAV; tải kết quả về dưới dạng `echo.wav`.
- **Phân tích hệ thống:** sơ đồ khối, đáp ứng xung h[n], đáp ứng tần số, giản đồ cực–không, phổ FFT của tín hiệu vào/ra.
- **Thử độ ổn định:** cho phép đặt `|α| ≥ 1` để thấy hệ IIR mất ổn định (cực ra ngoài đường tròn đơn vị).
- **Kiểm chứng cài đặt:** so sánh cài đặt từng mẫu (bộ đệm vòng), cài đặt theo khối (numpy) với `scipy.signal.lfilter`.
- **Có phương án dự phòng:** `demo_cli.py` chạy không cần trình duyệt.

## 🧮 Các mô hình

Gọi D = round(τ · Fs) là độ trễ tính bằng số mẫu (ví dụ τ = 300 ms, Fs = 22 050 Hz → D = 6 615 mẫu)
và α là hệ số suy giảm của tiếng vọng.

| Mô hình | Phương trình sai phân | H(z) | Ổn định BIBO |
|---|---|---|---|
| 1 tiếng vọng (FIR) | y[n] = x[n] + α·x[n−D] | 1 + α·z^(−D) | Luôn luôn |
| N tiếng vọng (FIR) | y[n] = Σ α^k·x[n−kD], k = 0..N | Σ α^k·z^(−kD) | Luôn luôn |
| Vọng lặp vô hạn (IIR) | y[n] = x[n] + α·y[n−D] | 1 / (1 − α·z^(−D)) | Khi trị tuyệt đối của α nhỏ hơn 1 |

Đáp ứng xung của ba mô hình (α = 0.6, D = 8, N = 3):

> **Đáp ứng xung của ba mô hình** — Hình được tạo bằng `python demo_cli.py --no-play` (lưu tại `figures/impulse_responses.png`).

Cả ba đều là bộ lọc **răng lược (comb filter)**: đáp ứng biên độ tuần hoàn với chu kỳ 2π/D,
tức các đỉnh cách nhau Fs/D Hz.

> **Đáp ứng tần số dạng răng lược của FIR và IIR** — Hình được tạo bằng `python demo_cli.py --no-play` (lưu tại `figures/frequency_response.png`).

Với IIR, D cực nằm trên đường tròn bán kính |α|^(1/D), nên hệ chỉ ổn định khi |α| < 1.

> **Giản đồ cực–không: FIR, IIR ổn định, IIR không ổn định** — Hình được tạo bằng `python demo_cli.py --no-play` (lưu tại `figures/pole_zero.png`).

## 🚀 Cài đặt và chạy

Yêu cầu **Python 3.10+**.

```bash
git clone https://github.com/ttminhhayamin/Digital-Echo-Effect.git
cd Digital-Echo-Effect
python -m pip install -r requirements.txt
```

Chạy ứng dụng demo:

```bash
python -m streamlit run app.py
```

Trình duyệt mở tại `http://localhost:8501`. Trên Windows có thể nhấp đúp `run_demo.bat` để tự cài thư viện và mở ứng dụng.

Chạy bản dòng lệnh (không cần trình duyệt): phát âm gốc và các bản có echo qua loa
(trên Windows), đồng thời lưu file WAV vào `output/` và hình vào `figures/`:

```bash
python demo_cli.py            # có phát âm thanh
python demo_cli.py --no-play  # chỉ tạo file
python demo_cli.py --delay 250 --alpha 0.7
```

## 📁 Cấu trúc dự án

```
.
├── app.py             # Giao diện demo Streamlit (3 tab)
├── echo_dsp.py        # Lõi DSP: 3 mô hình, cài đặt từng mẫu và theo khối, h[n], H(e^jω), cực–không
├── diagrams.py        # Vẽ sơ đồ khối (bộ cộng, bộ nhân, phần tử trễ)
├── demo_cli.py        # Demo dòng lệnh và script tạo hình minh họa
├── run_demo.bat       # Chạy nhanh trên Windows
├── requirements.txt
├── figures/           # Hình minh họa
├── DEMO_GUIDE.md      # Kịch bản demo và câu hỏi thường gặp
├── PROJECT_REPORT.md  # Báo cáo kỹ thuật đầy đủ (tiếng Anh): lý thuyết, cài đặt, kết quả
└── .streamlit/        # Cấu hình giao diện Streamlit
```

## 🧪 Cách cài đặt trong `echo_dsp.py`

Có hai cách tính cho cùng một hệ thống, cho kết quả trùng với `scipy.signal.lfilter` (sai số cỡ 1e-16):

- `echo_direct`: tính từng mẫu với bộ đệm vòng chứa D mẫu, mỗi mẫu cần một phép nhân và một phép cộng,
  giống cách chạy thời gian thực trên chip DSP. Chậm trong Python, dùng để kiểm chứng và giải thích.
- `echo_fast`: tính theo khối bằng numpy. Với IIR, vì phản hồi trễ đúng D mẫu nên mỗi khối D mẫu chỉ phụ thuộc khối liền trước.

## 📚 Kiến thức môn học được áp dụng

| Chương | Nội dung | Áp dụng trong dự án |
|---|---|---|
| 2 | Phương trình sai phân, sơ đồ khối | Mô hình echo, bộ cộng/nhân/trễ |
| 3 | Biến đổi z, cực–không, ổn định BIBO | H(z) và điều kiện ổn định của IIR |
| 5 | Đáp ứng tần số, bộ lọc răng lược | \|H(e^jω)\| tuần hoàn chu kỳ 2π/D |
| 6 | Lấy mẫu | D = round(τ · Fs) |
| 7–8 | DFT, FFT | Phổ tín hiệu vào/ra |
| 9 | Cài đặt hệ FIR/IIR | Dạng trực tiếp, bộ đệm vòng |

## 🛠️ Công nghệ

Python · NumPy · SciPy · Matplotlib · Streamlit

## 🔭 Hướng phát triển

- Reverb kiểu Schroeder (nhiều comb filter song song kết hợp all-pass).
- Xử lý thời gian thực từ luồng micro.
- Echo stereo luân phiên trái/phải (ping-pong).

## 👤 Tác giả

Trần Tuấn Minh · Phạm Đặng Khánh Duy - Nguyễn Duy An
