# Hướng dẫn demo trước giảng viên

Tài liệu phụ trợ cho buổi bảo vệ: kịch bản demo khoảng 5 phút và các câu hỏi thường gặp.
Cách cài đặt và chạy ứng dụng xem trong [README.md](README.md).

## Kịch bản demo (~5 phút)

Mở sẵn ứng dụng trước khi lên thuyết trình. Bật loa đủ to.

1. **Tab "Demo âm thanh"**, nguồn = *Âm thanh mẫu*, chọn **Tiếng vỗ tay**.
   Mô hình = *1 tiếng vọng (FIR)*, τ = 300 ms, α = 0.6.
   Bấm phát **Âm gốc** rồi **Có echo** → nghe được 1 tiếng vọng.
   Chỉ vào đồ thị dạng sóng: tiếng vọng xuất hiện đúng tại đường đứt đỏ, cách D mẫu.
2. Đổi sang *Vọng lặp vô hạn (IIR)* → nghe chuỗi tiếng vọng nhỏ dần.
   Kéo α lên 0.9 → tiếng vọng kéo dài hơn. Kéo τ xuống 50 ms → nghe giống tiếng vang trong phòng.
3. Chọn **Giai điệu Đô-Mi-Son-Đô** với IIR → thấy echo trên nhạc.
4. Nguồn = *Ghi âm bằng micro* → nói "Xin chào thầy cô" → nghe giọng mình có echo.
   (Lần đầu trình duyệt sẽ hỏi quyền micro: bấm Allow.)
5. Mở mục **Phổ tần số (FFT)** → hình bên phải phóng to cho thấy các răng lược cách nhau Fs/D Hz.
6. **Tab "Phân tích hệ thống"**: sơ đồ khối, h[n], |H(e^jω)| và giản đồ cực–không (D nhỏ để nhìn rõ).
   Với IIR: tích ô **"Cho phép |α| ≥ 1"**, kéo α = 1.05 → cực ra ngoài đường tròn đơn vị,
   cảnh báo đỏ, quay lại tab Demo thấy biên độ tăng dần → hệ **không ổn định**.
7. **Tab "Kiểm chứng cài đặt"** → bấm *Chạy kiểm chứng* → 3 cách cài đặt cho sai số ~1e-16.
   Mở "Xem mã nguồn echo_direct" để giải thích bộ đệm vòng.

**Phương án dự phòng:** nếu trình duyệt hoặc micro trục trặc, chạy `python demo_cli.py`
(tự phát âm gốc rồi bản có echo qua loa) hoặc mở sẵn các file trong `output/` bằng trình nghe nhạc.

## Câu hỏi giảng viên có thể hỏi

- **Vì sao FIR luôn ổn định?** h[n] hữu hạn ⇒ Σ|h[n]| = 1 + |α| < ∞ (BIBO). Mọi cực của H(z) đều ở z = 0.
- **Điều kiện ổn định của IIR?** Cực là nghiệm z^D = α ⇒ |p| = |α|^(1/D). Ổn định ⇔ |p| < 1 ⇔ |α| < 1.
  Khi đó Σ|h[n]| = 1/(1−|α|) < ∞.
- **Vì sao gọi là bộ lọc răng lược?** |H(e^jω)|² = 1 + α² + 2α·cos(ωD) (FIR), tuần hoàn với chu kỳ 2π/D:
  có D đỉnh và D khe trên [0, 2π). Theo Hz, các đỉnh cách nhau Fs/D.
- **Độ trễ thực tế bao nhiêu thì nghe thành echo?** Khoảng từ 50 ms trở lên; ngắn hơn thì tai nghe thành tiếng vang/âm sắc bị nhuộm (hiệu ứng comb), không tách thành tiếng riêng.
- **α âm nghĩa là gì?** Tiếng vọng bị đảo pha; đỉnh của răng lược dời sang ω = (2k+1)π/D.
- **Cần bao nhiêu bộ nhớ?** D mẫu cho FIR 1 tiếng vọng và IIR; N·D mẫu cho FIR N tiếng vọng.
  D = 6 615 mẫu × 2 byte ≈ 13 KB.
- **Vì sao không dùng lfilter cho âm thanh dài?** lfilter duyệt toàn bộ D+1 hệ số (phần lớn bằng 0),
  với D hàng nghìn sẽ rất chậm. `echo_fast` tận dụng cấu trúc thưa: IIR tính theo từng khối D mẫu,
  vì khối hiện tại chỉ phụ thuộc khối liền trước.
- **Hệ có tuyến tính, bất biến không?** Có: chỉ gồm cộng, nhân hằng số và trễ (Chương 2).
- **Mở rộng?** Reverb kiểu Schroeder (nhiều comb filter song song + all-pass nối tiếp), echo stereo ping-pong, xử lý thời gian thực.