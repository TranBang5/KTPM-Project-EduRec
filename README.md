# Student Study Plan Recommendation System

Hệ thống đề xuất kế hoạch học tập cho học sinh sử dụng Machine Learning và kiến trúc Microservices.

## 🏗️ Kiến trúc

Hệ thống sử dụng kiến trúc **Microservices** với 7 services độc lập:

- **API Gateway** (Port 5000) - Entry point duy nhất
- **Auth Service** (Port 5004) - Authentication & Authorization
- **Catalog Service** (Port 5005) - Quản lý Courses/Tutors/Materials
- **Profile Service** (Port 5006) - Quản lý User Profile
- **Recommendation Service** (Port 5001) - ML Recommendations
- **Study Plan Service** (Port 5002) - Quản lý Study Plans
- **Feedback Service** (Port 5003) - Thu thập Feedback

## 🚀 Cách chạy

### Yêu cầu
- Docker và Docker Compose
- Python 3.9+ (cho app chính)

### Chạy với Docker Compose (Khuyến nghị)

**Từ folder root của project:**

```bash
# Windows (PowerShell)
.\start.ps1

# Linux/Mac hoặc Git Bash trên Windows
./start.sh

# Hoặc trực tiếp với Docker Compose
docker-compose up -d --build
```

Lệnh này sẽ:
- ✅ Start MySQL database
- ✅ Build và start tất cả 7 microservices
- ✅ Setup network và dependencies

### Kiểm tra services

```bash
# Check tất cả services
docker-compose ps

# Check health của API Gateway
curl http://localhost:5000/health

# Check logs
docker-compose logs -f

# Check logs của service cụ thể
docker-compose logs -f api-gateway
docker-compose logs -f recommendation-service
```

### Chạy Application chính

Sau khi microservices đã chạy, start app chính:

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
python app.py
```

App sẽ chạy tại: http://localhost:5000

## 📁 Cấu trúc Project

```
.
├── docker-compose.yml          # Docker Compose config (chạy từ đây)
├── app.py                      # Main application
├── microservices/              # Tất cả microservices
│   ├── api_gateway/
│   ├── auth_service/
│   ├── catalog_service/
│   ├── profile_service/
│   ├── recommendation_service/
│   ├── study_plan_service/
│   └── feedback_service/
├── models/                     # Shared database models
├── data/                       # Training data
├── templates/                  # HTML templates
└── static/                     # CSS, JS
```

## 🔧 Cấu hình

### Environment Variables

Tạo file `.env` trong root:

```env
# Database
DATABASE_URL=mysql+mysqlconnector://user:password@db:3306/recommendation_db

# Secrets
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# API Gateway URL
API_GATEWAY_URL=http://localhost:5000
```

### Database Configuration

Database được tự động setup trong Docker Compose:
- **Host**: `db` (trong Docker network) hoặc `localhost:3306` (từ host)
- **Database**: `recommendation_db`
- **User**: `user`
- **Password**: `password`
- **Root Password**: `rootpassword`

**⚠️ Lưu ý**: Thay đổi passwords trong production!

## 📊 Services Endpoints

### API Gateway (http://localhost:5000)
- `GET /health` - Health check tất cả services
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập
- `GET /profiles/{user_id}` - Lấy profile
- `POST /recommendations/generate` - Tạo recommendations
- `POST /study-plans` - Tạo study plan
- `POST /feedback` - Gửi feedback
- Và nhiều endpoints khác...

Xem chi tiết trong `microservices/README.md`

## 🛠️ Development

### Rebuild services sau khi thay đổi code

```bash
docker-compose up -d --build <service-name>
```

### Restart service

```bash
docker-compose restart <service-name>
```

### Stop tất cả services

```bash
docker-compose down
```

### Stop và xóa volumes

```bash
docker-compose down -v
```

## 📚 Documentation

- `microservices/README.md` - Chi tiết về microservices
- `microservices/SERVICES_STRUCTURE.md` - Cấu trúc từng service
- `MICROSERVICES_MIGRATION_PLAN.md` - Kế hoạch migration chi tiết

## 🧪 Testing

### Test API Gateway

```bash
curl http://localhost:5000/health
```

### Test Auth Service

```bash
# Register
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## ⚠️ Troubleshooting

### Services không start

```bash
# Check logs
docker-compose logs

# Check status
docker-compose ps

# Restart tất cả
docker-compose restart
```

### Database connection issues

```bash
# Check database container
docker-compose ps db

# Check database logs
docker-compose logs db

# Access database
docker-compose exec db mysql -u user -ppassword recommendation_db
```

### Port conflicts

Nếu ports đã được sử dụng, thay đổi trong `docker-compose.yml`:

```yaml
ports:
  - "5000:5000"  # Thay đổi port đầu tiên
```

## 📝 Notes

- Tất cả services chạy trong Docker network `microservices-network`
- Database data được persist trong Docker volume `mysql_data`
- Volumes mount trực tiếp từ host để development dễ dàng
- Services tự động restart nếu crash (restart: unless-stopped)

## 🚀 Production Deployment

Cho production, cần:
- ✅ Thay đổi tất cả default passwords
- ✅ Setup SSL/TLS
- ✅ Configure proper logging
- ✅ Setup monitoring và alerting
- ✅ Database backup strategy
- ✅ Load balancing cho API Gateway