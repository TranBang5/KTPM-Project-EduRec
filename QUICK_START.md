# 🚀 Quick Start Guide

Hướng dẫn nhanh để chạy hệ thống từ folder root.

## ⚡ Cách chạy nhanh nhất

### 1. Start Microservices

```bash
# Windows (PowerShell)
.\start.ps1

# Linux/Mac
./start.sh

# Hoặc
docker-compose up -d --build
```

### 2. Kiểm tra Services

```bash
# Check tất cả services
docker-compose ps

# Check health
curl http://localhost:5000/health
```

### 3. Start Application

```bash
python app.py
```

Truy cập: http://localhost:5000

## 📋 Cấu trúc Docker Compose

File `docker-compose.yml` ở **root folder** bao gồm:

- ✅ **Database** (MySQL) - Tự động setup
- ✅ **7 Microservices** - Tất cả services
- ✅ **Networks & Volumes** - Được config sẵn

## 🔧 Cấu hình nhanh

### Tạo file .env (nếu cần)

```bash
cp .env.example .env
# Sau đó edit .env với thông tin của bạn
```

### Default Configuration

Docker Compose đã được config với:
- Database: `recommendation_db` (user: `user`, password: `password`)
- All services expose trên localhost với ports riêng
- Volumes mount trực tiếp từ host

## ⚠️ Lưu ý

1. **Chạy từ root**: Luôn chạy `docker-compose` từ folder root
2. **Database**: Tự động tạo khi lần đầu chạy
3. **Ports**: Đảm bảo ports 5000-5006 và 3306 không bị chiếm
4. **Volumes**: Models, data được mount từ host

## 🛠️ Common Commands

```bash
# Start tất cả
docker-compose up -d

# Stop tất cả
docker-compose down

# Restart service
docker-compose restart <service-name>

# View logs
docker-compose logs -f

# Rebuild và start
docker-compose up -d --build
```

## 🎯 Next Steps

1. ✅ Start Docker Compose: `docker-compose up -d --build`
2. ✅ Wait for services ready (~30 seconds)
3. ✅ Check health: `curl http://localhost:5000/health`
4. ✅ Start app: `python app.py`
5. ✅ Access: http://localhost:5000
