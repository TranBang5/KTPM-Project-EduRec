# Auth Service

Microservice xử lý authentication và authorization cho hệ thống Student Study Plan Recommendation.

## Tính năng

- ✅ Đăng ký tài khoản
- ✅ Đăng nhập/Đăng xuất
- ✅ JWT Access Token (1 giờ)
- ✅ JWT Refresh Token (7 ngày)
- ✅ Quên mật khẩu (gửi email reset)
- ✅ Quản lý profile người dùng
- ✅ Verify token

## API Endpoints

### Authentication
- `POST /auth/register` - Đăng ký tài khoản
- `POST /auth/login` - Đăng nhập
- `POST /auth/refresh` - Làm mới access token

### Password Reset
- `POST /auth/forgot-password` - Gửi email reset password
- `POST /auth/reset-password` - Reset password với token

### Profile Management
- `GET /auth/profile` - Lấy thông tin profile
- `PUT /auth/profile` - Cập nhật profile

### Utility
- `POST /auth/verify-token` - Verify JWT token
- `GET /auth/health` - Health check

## Cấu trúc

```
services/auth/
├── __init__.py          # Blueprint initialization
├── routes.py            # API routes
├── jwt_utils.py         # JWT helper functions
├── config.py            # Configuration
└── README.md            # Documentation
```

## JWT Token Format

### Access Token
```json
{
  "user_id": 1,
  "type": "access",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Refresh Token
```json
{
  "user_id": 1,
  "type": "refresh",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Request/Response Examples

### Register
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "school": "ABC School",
  "current_grade": "Lớp 10",
  "learning_goals": "Học tốt toán",
  "favorite_subjects": "Toán, Lý",
  "preferred_learning_method": "online"
}
```

### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Refresh Token
```bash
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
