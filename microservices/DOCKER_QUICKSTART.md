# Hướng dẫn Chạy với Docker (Không cần setup_services.py)

## 🐳 Chạy chỉ với Docker

Nếu bạn **chỉ muốn chạy với Docker**, bạn **KHÔNG CẦN** chạy `setup_services.py`!

### Tại sao?

Docker Compose đã được cấu hình với **volumes** để tự động mount các file/thư mục cần thiết từ root project vào các containers:

- ✅ `models/` → Mount vào auth, catalog, profile, recommendation services
- ✅ `data/` → Mount vào recommendation service
- ✅ `checkpoints/` → Mount vào recommendation service  
- ✅ `bruteforce_data.npz` → Mount vào recommendation service

## 🚀 Các bước chạy

### 1. Đảm bảo có database
Nếu chưa có database service trong docker-compose, bạn cần:
- Chạy MySQL database riêng, hoặc
- Thêm database service vào docker-compose.yml

### 2. Chạy tất cả services
```bash
cd microservices
docker-compose up --build
```

Hoặc chạy ở background:
```bash
docker-compose up -d --build
```

### 3. Kiểm tra services
```bash
# Check tất cả services
curl http://localhost:5000/health

# Check từng service
curl http://localhost:5001/health  # Recommendation
curl http://localhost:5002/health  # Study Plan
curl http://localhost:5003/health  # Feedback
curl http://localhost:5004/health  # Auth
curl http://localhost:5005/health  # Catalog
curl http://localhost:5006/health  # Profile
```

## 📋 Volumes trong docker-compose.yml

### Recommendation Service
```yaml
volumes:
  - ../models:/app/models              # Database models
  - ../data:/app/data                  # Training data
  - ../checkpoints:/app/checkpoints    # Model weights
  - ../bruteforce_data.npz:/app/bruteforce_data.npz  # BruteForce data
```

### Auth, Catalog, Profile Services
```yaml
volumes:
  - ../models:/app/models  # Database models
```

### Study Plan & Feedback Services
Không cần volumes (dùng in-memory storage)

## 🔍 So sánh: Setup Script vs Docker Volumes

| Phương pháp | Khi nào dùng | Ưu điểm |
|------------|--------------|---------|
| **setup_services.py** | Chạy local (không Docker) | Copy files vào từng service |
| **Docker Volumes** | Chạy với Docker | Tự động sync, không cần copy |

## ⚠️ Lưu ý

1. **Đường dẫn volumes**: Dùng relative paths (`../models`) nên cần chạy từ thư mục `microservices/`

2. **Database**: Đảm bảo database đang chạy và accessible từ containers

3. **File paths trong code**: 
   - Code trong containers đọc từ `/app/models`, `/app/data`, etc.
   - Docker tự động map từ `../models`, `../data` trên host

4. **Nếu thiếu files**: 
   - Docker sẽ tạo empty directories
   - Services có thể fail nếu thiếu files quan trọng (như models, data)

## 🔧 Troubleshooting

### Services không tìm thấy files
```bash
# Kiểm tra volumes đã mount chưa
docker-compose exec recommendation-service ls -la /app/models
docker-compose exec recommendation-service ls -la /app/data
```

### Muốn update files
- Chỉ cần update files trên host (`../models`, `../data`)
- Docker tự động sync vào containers (real-time)

### Restart services sau khi thay đổi code
```bash
docker-compose restart <service-name>
# hoặc
docker-compose up -d --build <service-name>
```

## ✅ Tóm tắt

**Nếu chỉ chạy Docker:**
- ❌ KHÔNG cần chạy `setup_services.py`
- ✅ Chỉ cần `docker-compose up --build`
- ✅ Files tự động mount qua volumes
- ✅ Đơn giản và nhanh hơn!


