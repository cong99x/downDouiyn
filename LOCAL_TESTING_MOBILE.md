# 📱 Hướng dẫn Test tải video trên Mobile (Local Network)

Để kiểm tra tính năng tải xuống trên điện thoại khi chạy máy tính ở local, bạn cần thực hiện các bước sau:

## 1. Yêu cầu hệ thống
* Máy tính và Điện thoại phải kết nối cùng một mạng WiFi.
* Cho phép các cổng **3000** (Frontend) và **5000** (Backend) qua tường lửa (Firewall) của Windows.

## 2. Tìm Địa chỉ IP của máy tính
1. Mở **Command Prompt (cmd)** trên máy tính.
2. Gõ lệnh `ipconfig`.
3. Tìm dòng **IPv4 Address** (ví dụ: `192.168.1.10`).

## 3. Khởi chạy Backend (Port 5000)
1. Đảm bảo file `backend/app.py` đang lắng nghe ở host `0.0.0.0` (đã cấu hình sẵn).
2. Chạy backend:
   ```bash
   python backend/app.py
   ```

## 4. Khởi chạy Frontend (với flag --host)
1. Chạy Vite với flag `--host` để mở rộng truy cập ra ngoài localhost:
   ```bash
   npm run dev -- --host
   ```
2. Vite sẽ hiển thị địa chỉ LAN (ví dụ: `http://192.168.1.10:3000`).

## 5. Thử nghiệm trên Điện thoại
1. Mở trình duyệt (Safari trên iPhone hoặc Chrome trên Android).
2. Nhập địa chỉ LAN (ví dụ: `http://192.168.1.10:3000`).
3. Dán link video Douyin và nhấn tải.

### 💡 Lưu ý quan trọng:
* **HTTPS vs HTTP:** Nếu bạn truy cập frontend qua một link HTTPS (như Vercel) nhưng backend là HTTP (local), trình duyệt mobile sẽ chặn vì lỗi **Mixed Content**. Hãy đảm bảo cả 2 đều dùng **HTTP** khi test local.
* **Quyền lưu file:** Trên Safari iPhone, khi nhấn tải xong, máy sẽ hỏi "Bạn có muốn tải xuống video.mp4 không?". Hãy nhấn **Tải về**. Video sẽ nằm trong ứng dụng **Tệp (Files)** hoặc **Tải về (Downloads)**.

---
**Các cải tiến đã thực hiện trong code:**
- **S3 Bypass:** Hệ thống nhận diện bạn không dùng S3 nên sẽ ưu tiên phục vụ file trực tiếp từ Render/Local.
- **Auto-Download:** Sau khi xử lý xong, video sẽ tự động kích hoạt tải xuống sau 0.8 giây.
- **Mobile-friendly Trigger:** Sử dụng `window.location.href` thay vì giả lập click thẻ `<a>` để vượt qua các bộ lọc bảo mật của Safari/Chrome mobile.
- **Byte-Range Support:** Backend đã hỗ trợ `conditional=True` giúp việc tải file lớn trên mobile mượt mà và ổn định hơn.
