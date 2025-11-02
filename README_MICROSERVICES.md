# 🚀 Student Study Plan Recommendation System - Microservices Architecture

Hệ thống đã được **chuyển đổi hoàn toàn** sang kiến trúc **Microservices**.

## ⚠️ THAY ĐỔI QUAN TRỌNG

- ❌ **Không còn hỗ trợ Monolith**: App.py chính giờ gọi microservices qua API Gateway
- ✅ **Yêu cầu Docker Compose**: Hệ thống cần tất cả microservices chạy
- ✅ **API Gateway**: Tất cả requests đi qua API Gateway (port 5000)

## 📋 Kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                     │
│                    (app.py - Port 5000)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                           │
│                    (Port 5000)                           │
└────┬──────────┬──────────┬──────────┬──────────┬────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  Auth   │ │Recommend│ │StudyPlan│ │Feedback │ │Catalog  │
│ Service │ │ Service │ │ Service │ │ Service │ │ Service │
│  :5004  │ │  :5001  │ │  :5002  │ │  :5003  │ │  :5005  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │
     ▼
┌─────────┐
│ Profile │
│ Service │
│  :5006  │
└─────────┘
```

## 🚀 Cách Chạy

### 1. Start Microservices
```bash
cd microservices
docker-compose up -d --build
```

### 2. Start Main Application
```bash
# Từ root directory
python app.py
# hoặc
flask run
```

### 3. Access Application
- Web UI: http://localhost:5000
- API Gateway: http://localhost:5000/health

## 📁 Cấu trúc Project

```
.
├── app.py                    # Main app (uses microservices via API Gateway)
├── microservices/            # All microservices
│   ├── api_gateway/
│   ├── auth_service/
│   ├── recommendation_service/
│   ├── study_plan_service/
│   ├── feedback_service/
│   ├── catalog_service/
│   ├── profile_service/
│   └── docker-compose.yml
├── models/                   # Shared database models
├── templates/                # HTML templates
├── static/                   # CSS, JS
└── data/                     # Training data
```

## 🔧 Configuration

### Environment Variables

Tạo file `.env`:

```env
# API Gateway URL
API_GATEWAY_URL=http://localhost:5000

# Database
DATABASE_URL=mysql+mysqlconnector://user:password@db:3306/recommendation_db
SECRET_KEY=your-secret-key

# Services (optional, defaults to localhost)
RECOMMENDATION_SERVICE_URL=http://localhost:5001
STUDY_PLAN_SERVICE_URL=http://localhost:5002
FEEDBACK_SERVICE_URL=http://localhost:5003
AUTH_SERVICE_URL=http://localhost:5004
CATALOG_SERVICE_URL=http://localhost:5005
PROFILE_SERVICE_URL=http://localhost:5006
```

## 📚 Documentation

- `microservices/README.md` - Chi tiết về microservices
- `microservices/DOCKER_QUICKSTART.md` - Hướng dẫn Docker
- `microservices/SERVICES_STRUCTURE.md` - Cấu trúc từng service
- `microservices/MIGRATION_SUMMARY.md` - Tóm tắt migration

## 🧹 Cleanup

Nếu muốn clean up hoàn toàn:

```bash
python cleanup_to_microservices.py
```

Script này sẽ:
1. Backup app.py cũ
2. Replace với version microservices
3. Archive folder services/

## ⚠️ Troubleshooting

### Services không chạy
```bash
cd microservices
docker-compose ps
docker-compose logs -f
```

### API Gateway không accessible
```bash
curl http://localhost:5000/health
```

### Check từng service
```bash
curl http://localhost:5001/health  # Recommendation
curl http://localhost:5004/health  # Auth
# ... etc
```

## 🔄 Migration từ Monolith

Nếu bạn đang migrate từ monolith:

1. Backup code hiện tại
2. Chạy `cleanup_to_microservices.py`
3. Start Docker Compose
4. Test các chức năng

## 📝 Notes

- **Folder `services/`**: Đã được archive, có thể xóa sau khi xác nhận
- **Backup files**: Trong `backup/` và `archive/` directories
- **Database**: Vẫn dùng chung (sẽ tách riêng trong tương lai)
