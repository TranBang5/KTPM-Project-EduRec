# Microservices Architecture

Hệ thống Student Study Plan Recommendation đã được migrate từ kiến trúc Monolith sang kiến trúc Microservices với 3 service chính: Recommendation, Study Plan và Feedback.

## Cấu trúc Services

### 1. Recommendation Service (Port 5001)
- **Chức năng**: Cung cấp các gợi ý về kế hoạch học tập dựa trên mô hình Machine Learning
- **Endpoints**:
  - `POST /recommendations/generate` - Tạo đề xuất cho người dùng
  - `GET /recommendations/models` - Thông tin về mô hình
  - `GET /health` - Health check

### 2. Study Plan Service (Port 5002)
- **Chức năng**: Quản lý kế hoạch học tập chi tiết của người dùng
- **Endpoints**:
  - `POST /study-plans` - Tạo kế hoạch học tập mới
  - `GET /study-plans/{user_id}` - Lấy kế hoạch học tập của người dùng
  - `POST /study-plans/{user_id}/items` - Thêm mục vào kế hoạch
  - `PUT /study-plans/{user_id}/items/{item_id}` - Cập nhật mục trong kế hoạch
  - `DELETE /study-plans/{user_id}/items/{item_id}` - Xóa mục khỏi kế hoạch
  - `GET /study-plans/{user_id}/schedule` - Lấy lịch học đã sắp xếp
  - `GET /health` - Health check

### 3. Feedback Service (Port 5003)
- **Chức năng**: Thu thập và phân tích phản hồi từ người dùng
- **Endpoints**:
  - `POST /feedback` - Gửi phản hồi
  - `GET /feedback/{user_id}` - Lấy phản hồi của người dùng
  - `PUT /feedback/{feedback_id}` - Cập nhật trạng thái phản hồi
  - `GET /feedback/analytics` - Phân tích phản hồi tổng quan
  - `GET /feedback/analytics/{user_id}` - Phân tích phản hồi của người dùng
  - `GET /feedback/reports` - Tạo báo cáo phản hồi
  - `GET /health` - Health check

### 4. API Gateway (Port 5000)
- **Chức năng**: Điểm vào duy nhất cho tất cả các request từ client
- **Tính năng**:
  - Routing requests đến các microservice tương ứng
  - Health checking cho tất cả services
  - Error handling và fallback
  - Load balancing (có thể mở rộng)

## Cài đặt và Chạy

### 1. Chuẩn bị
```bash
# Copy các file cần thiết
python setup_services.py
```

### 2. Chạy với Docker Compose
```bash
# Build và chạy tất cả services
docker-compose up --build

# Chạy trong background
docker-compose up -d --build

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down
```

### 3. Chạy từng service riêng lẻ
```bash
# Recommendation Service
cd recommendation_service
python app.py

# Study Plan Service
cd study_plan_service
python app.py

# Feedback Service
cd feedback_service
python app.py

# API Gateway
cd api_gateway
python app.py
```

## Cấu hình Environment Variables

Tạo file `.env` trong thư mục microservices:

```env
# Database
DATABASE_URL=mysql+mysqlconnector://user:password@db:3306/recommendation_db
SECRET_KEY=your-secret-key

# Service URLs (for API Gateway)
RECOMMENDATION_SERVICE_URL=http://localhost:5001
STUDY_PLAN_SERVICE_URL=http://localhost:5002
FEEDBACK_SERVICE_URL=http://localhost:5003

# Recommendation Service
WEIGHTS_DIR=./checkpoints
BRUTEFORCE_DATA_PATH=./bruteforce_data.npz
```

## Migration từ Monolith

### Bước 1: Backup dữ liệu
```bash
# Backup database
mysqldump -u user -p recommendation_db > backup.sql
```

### Bước 2: Chạy microservices
```bash
# Chạy microservices
docker-compose up -d --build
```

### Bước 3: Cập nhật app.py
Thay thế `app.py` hiện tại bằng `migrated_app.py`:

```bash
# Backup app.py hiện tại
cp app.py app_monolith_backup.py

# Sử dụng migrated app
cp microservices/migrated_app.py app.py
```

### Bước 4: Test hệ thống
```bash
# Test API Gateway
curl http://localhost:5000/health

# Test Recommendation Service
curl http://localhost:5001/health

# Test Study Plan Service
curl http://localhost:5002/health

# Test Feedback Service
curl http://localhost:5003/health
```

## Monitoring và Logging

### Health Checks
Tất cả services đều có endpoint `/health` để kiểm tra trạng thái:

```bash
# Kiểm tra tất cả services
curl http://localhost:5000/health
```

### Logs
```bash
# Xem logs của tất cả services
docker-compose logs -f

# Xem logs của service cụ thể
docker-compose logs -f recommendation-service
docker-compose logs -f study-plan-service
docker-compose logs -f feedback-service
docker-compose logs -f api-gateway
```

## Lợi ích của Kiến trúc Microservices

1. **Scalability**: Có thể scale từng service độc lập
2. **Reliability**: Lỗi ở một service không ảnh hưởng toàn bộ hệ thống
3. **Maintainability**: Dễ dàng phát triển và bảo trì từng service
4. **Technology Flexibility**: Có thể sử dụng công nghệ khác nhau cho từng service
5. **Development Velocity**: Các team có thể phát triển song song

## Troubleshooting

### Service không khởi động
```bash
# Kiểm tra logs
docker-compose logs [service-name]

# Restart service
docker-compose restart [service-name]
```

### Database connection issues
- Kiểm tra DATABASE_URL trong .env
- Đảm bảo database service đang chạy
- Kiểm tra network connectivity

### Model loading issues
- Đảm bảo checkpoints và data files được copy đúng
- Kiểm tra WEIGHTS_DIR và BRUTEFORCE_DATA_PATH
- Xem logs của recommendation-service

## Mở rộng trong tương lai

1. **Database per Service**: Tách database riêng cho từng service
2. **Message Queue**: Sử dụng Redis/RabbitMQ cho async communication
3. **Service Discovery**: Sử dụng Consul hoặc Eureka
4. **API Versioning**: Hỗ trợ multiple API versions
5. **Caching**: Thêm Redis cache cho performance
6. **Monitoring**: Tích hợp Prometheus + Grafana
7. **Logging**: Centralized logging với ELK Stack
