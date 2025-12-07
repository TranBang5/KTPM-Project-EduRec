# Cấu trúc Microservices - Tổng hợp

## 📋 Tổng quan

Hệ thống đã được tổ chức lại với tất cả các microservices nằm trong thư mục `microservices/`. Các services từ folder `services/` (blueprints) đã được chuyển đổi thành standalone Flask applications.

## 🏗️ Cấu trúc Services

### 1. Auth Service (Port 5004)
**Vị trí**: `microservices/auth_service/`

**Chức năng**: Xử lý authentication và authorization
- User registration và login
- JWT token generation và verification
- Password reset
- Profile management (moved from auth to profile)

**Endpoints**:
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập
- `POST /auth/refresh` - Refresh token
- `POST /auth/forgot-password` - Quên mật khẩu
- `POST /auth/reset-password` - Reset mật khẩu
- `POST /auth/verify-token` - Verify JWT token
- `GET /auth/profile` - Lấy profile (deprecated, use profile service)
- `PUT /auth/profile` - Cập nhật profile (deprecated, use profile service)

### 2. Catalog Service (Port 5005)
**Vị trí**: `microservices/catalog_service/`

**Chức năng**: Quản lý danh mục (courses, tutors, materials)
- CRUD operations cho courses, tutors, materials
- Filtering và pagination
- Search functionality

**Endpoints**:
- `GET /catalog/courses` - Lấy danh sách courses
- `GET /catalog/courses/<id>` - Lấy course theo ID
- `POST /catalog/courses` - Tạo course mới
- `PUT /catalog/courses/<id>` - Cập nhật course
- `DELETE /catalog/courses/<id>` - Xóa course
- Similar endpoints for `/catalog/tutors` and `/catalog/materials`
- `GET /catalog/search?q=<term>` - Tìm kiếm tất cả

### 3. Profile Service (Port 5006)
**Vị trí**: `microservices/profile_service/`

**Chức năng**: Quản lý user profile
- Get và update profile
- Profile history (tương lai)

**Endpoints**:
- `GET /profiles/<user_id>` - Lấy profile
- `PUT /profiles/<user_id>` - Cập nhật profile
- `GET /profiles/<user_id>/history` - Lấy lịch sử thay đổi

### 4. Recommendation Service (Port 5001)
**Vị trí**: `microservices/recommendation_service/`

**Chức năng**: Tạo recommendations dựa trên ML model
- Generate recommendations
- Model management

**Endpoints**:
- `POST /recommendations/generate` - Tạo recommendations
- `GET /recommendations/models` - Thông tin model

### 5. Study Plan Service (Port 5002)
**Vị trí**: `microservices/study_plan_service/`

**Chức năng**: Quản lý kế hoạch học tập
- CRUD cho study plans và items
- Schedule management

**Endpoints**:
- `POST /study-plans` - Tạo study plan
- `GET /study-plans/<user_id>` - Lấy study plan
- `POST /study-plans/<user_id>/items` - Thêm item
- `PUT /study-plans/<user_id>/items/<item_id>` - Cập nhật item
- `DELETE /study-plans/<user_id>/items/<item_id>` - Xóa item
- `GET /study-plans/<user_id>/schedule` - Lấy lịch học

### 6. Feedback Service (Port 5003)
**Vị trí**: `microservices/feedback_service/`

**Chức năng**: Quản lý feedback
- Submit feedback
- Analytics và reports

**Endpoints**:
- `POST /feedback` - Gửi feedback
- `GET /feedback/<user_id>` - Lấy feedback của user
- `PUT /feedback/<feedback_id>` - Cập nhật status
- `GET /feedback/analytics` - Analytics tổng quan
- `GET /feedback/analytics/<user_id>` - Analytics của user
- `GET /feedback/reports` - Tạo báo cáo

### 7. API Gateway (Port 5000)
**Vị trí**: `microservices/api_gateway/`

**Chức năng**: Single entry point cho tất cả requests
- Routing đến các services
- Health checking
- Error handling

## 📁 Cấu trúc Thư mục

```
microservices/
├── api_gateway/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── auth_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── catalog_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── profile_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── recommendation_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── study_plan_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── feedback_service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── setup_services.py
├── run_migration.py
├── migrated_app.py
└── README.md
```

## 🔗 Service Communication

### Authentication Flow
1. User gửi request đến API Gateway
2. API Gateway route đến Auth Service
3. Auth Service tạo JWT token
4. Token được trả về cho client

### Authenticated Requests
1. Client gửi request với JWT token trong Authorization header
2. API Gateway forward request đến service tương ứng
3. Service (catalog, profile) verify token với Auth Service
4. Service xử lý request và trả về response

### Service Dependencies
- **Catalog Service** → Auth Service (token verification)
- **Profile Service** → Auth Service (token verification)
- **API Gateway** → Tất cả services (routing)

## 🚀 Cách sử dụng

### 1. Setup
```bash
cd microservices
python setup_services.py
```

### 2. Start với Docker Compose
```bash
docker-compose up -d --build
```

### 3. Health Check
```bash
curl http://localhost:5000/health
```

### 4. Test Auth Service
```bash
# Register
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password","full_name":"Test User"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### 5. Test Catalog Service
```bash
# Get courses (requires auth token)
curl -X GET http://localhost:5000/catalog/courses \
  -H "Authorization: Bearer <token>"
```

## 📝 Notes

- Tất cả services đều có `/health` endpoint
- Services sử dụng shared database (sẽ tách riêng trong tương lai)
- Models được copy vào các services cần thiết qua Docker volumes
- API Gateway là single entry point - tất cả requests đều đi qua đây
- Services communicate qua HTTP REST API

## ⚠️ Migration từ folder `services/`

Các services trong folder `services/` (auth, catalog, profile) là Flask blueprints được thiết kế để tích hợp vào một app duy nhất. Chúng đã được chuyển đổi thành standalone Flask applications trong `microservices/`:

- **auth** → `microservices/auth_service/`
- **catalog** → `microservices/catalog_service/`
- **profile** → `microservices/profile_service/`

Folder `services/` có thể được giữ lại cho tương thích ngược hoặc xóa sau khi migration hoàn tất.
