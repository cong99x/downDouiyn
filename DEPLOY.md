# Hướng dẫn Triển khai (Deployment Guide)

Hướng dẫn này sẽ giúp bạn đưa Douyin Downloader lên server (VPS) sử dụng Docker.

## 1. Chuẩn bị Server
Bạn cần một server (VPS) đã cài đặt:
- **Docker**
- **Docker Compose**
- **Git**

## 2. Các bước triển khai

### Bước 1: Tải mã nguồn về server
```bash
git clone https://github.com/your-username/douyin-downloader.git
cd douyin-downloader
```
*(Lưu ý: Thay `your-username` bằng tên tài khoản GitHub của bạn)*

### Bước 2: Cấu hình
Tạo file `config.yml` trên server (vì file này không được up lên GitHub để bảo mật).

```bash
# Copy từ file mẫu
cp config.example.yml config.yml

# Chỉnh sửa cấu hình AWS/MinIO
nano config.yml
```
Đảm bảo phần `aws` trong `config.yml` trỏ đúng tới MinIO (trong Docker network, backend có thể gọi minio là `minio` hoặc dùng IP host, nhưng với cấu hình hiện tại backend và minio cùng mạng docker `app_network` nên có thể dùng tên service `minio` nếu cần, hoặc dùng IP public của server nếu MinIO expose ra ngoài).

**QUAN TRỌNG:**
Trong môi trường Docker `docker-compose.prod.yml`, service backend gọi MinIO qua mạng nội bộ.
Tuy nhiên, cấu hình mặc định là `localhost`. Để backend trong docker gọi được minio trong docker, bạn có thể cần đổi `endpoint_url` trong `config.yml` thành `http://minio:9000`.

### Bước 3: Chạy ứng dụng
Sử dụng file `docker-compose.prod.yml` dành cho môi trường production:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Bước 4: Kiểm tra
- Truy cập Web: `http://<IP-Server>` (chạy trên cổng 80)
- Truy cập MinIO: `http://<IP-Server>:9001` (User/Pass: minioadmin)

## 3. Cập nhật phiên bản mới
Khi bạn có code mới đẩy lên GitHub, chỉ cần chạy:

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---
**Lưu ý về Bảo mật:**
- Đổi mật khẩu MinIO trong `docker-compose.prod.yml` nếu cần.
- Không commit `config.yml` lên GitHub.
