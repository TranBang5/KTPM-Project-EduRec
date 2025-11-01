# Kế hoạch Migration từ Monolith sang Microservices

## 📋 Tổng quan

Hệ thống Student Study Plan Recommendation hiện tại đang sử dụng kiến trúc Monolith với Flask, cần được migrate sang kiến trúc Microservices để cải thiện khả năng mở rộng, độ tin cậy và khả năng bảo trì.

## 🔍 Phân tích hệ thống hiện tại

### Kiến trúc Monolith hiện tại
```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Auth      │ │  Profile    │ │Recommendation│          │
│  │ Management  │ │ Management  │ │   Engine    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Catalog   │ │ Study Plan  │ │  Feedback   │          │
│  │ Management  │ │ Management  │ │ Management  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    MySQL Database                           │
│              (Single Database Instance)                    │
└─────────────────────────────────────────────────────────────┘
```

### Vấn đề hiện tại
- **Tight Coupling**: Tất cả logic trong 1 file `app.py` (1,297 dòng)
- **Single Point of Failure**: Lỗi ở bất kỳ chức năng nào đều ảnh hưởng toàn hệ thống
- **Scalability Issues**: Không thể scale từng component riêng biệt
- **Database Bottleneck**: 1 database cho tất cả services
- **No Caching**: Không có cache layer
- **No Load Balancing**: Không có khả năng phân tải

## 🏗️ Kiến trúc Microservices mới

### 1. API Gateway
```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Routing   │ │ JWT Verify  │ │Request/Resp │          │
│  │             │ │             │ │Transform    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Định tuyến request đến các microservices
- Xác thực JWT token
- Transform request/response format
- Rate limiting và throttling
- Load balancing

**Technology Stack:**
- **NGINX** hoặc **Kong** hoặc **Traefik**
- **Redis** cho session management

### 2. Auth Service
```
┌─────────────────────────────────────────────────────────────┐
│                  Auth Service                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Register   │ │   Login     │ │   Logout    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │JWT Generate │ │JWT Refresh  │ │Password     │          │
│  │             │ │             │ │Reset       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    auth_db                                 │
│  - users (id, email, password_hash, created_at)           │
│  - sessions (id, user_id, token, expires_at)              │
│  - refresh_tokens (id, user_id, token, expires_at)        │
│  - login_logs (id, user_id, ip, timestamp, success)       │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Đăng ký/đăng nhập người dùng
- Quản lý JWT tokens và refresh tokens
- Xác thực người dùng
- Quản lý phiên đăng nhập
- Reset mật khẩu

**API Endpoints:**
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

### 3. User Profile Service
```
┌─────────────────────────────────────────────────────────────┐
│              User Profile Service                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Get Profile │ │Update Profile│ │Delete Profile│         │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Profile      │ │Profile      │ │Profile      │          │
│  │Validation   │ │History      │ │Search       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   profile_db                               │
│  - profiles (id, user_id, school, grade, subjects, goals) │
│  - profile_history (id, profile_id, field, old_value,     │
│    new_value, changed_at)                                  │
│  - preferences (id, user_id, learning_method, subjects)   │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Quản lý hồ sơ học sinh
- Lưu trữ thông tin cá nhân và học tập
- Theo dõi lịch sử thay đổi profile
- Validation dữ liệu profile

**API Endpoints:**
- `GET /profiles/{user_id}`
- `PUT /profiles/{user_id}`
- `DELETE /profiles/{user_id}`
- `GET /profiles/{user_id}/history`
- `GET /profiles/search`

### 4. Catalog Service
```
┌─────────────────────────────────────────────────────────────┐
│                 Catalog Service                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Courses   │ │   Tutors    │ │  Materials  │          │
│  │ Management  │ │ Management  │ │ Management  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Search    │ │   Filter    │ │Pagination   │          │
│  │             │ │             │ │             │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   catalog_db                               │
│  - courses (id, name, subject, grade, method, time, cost) │
│  - tutors (id, name, subject, grade, method, experience)  │
│  - materials (id, name, subject, grade, type, description)│
│  - categories (id, name, type)                            │
│  - search_index (id, entity_type, entity_id, search_text) │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Quản lý danh mục courses, tutors, materials
- Tìm kiếm và lọc dữ liệu
- Phân trang kết quả
- Validation dữ liệu catalog
- Search indexing

**API Endpoints:**
- `GET /catalog/courses`
- `GET /catalog/tutors`
- `GET /catalog/materials`
- `GET /catalog/search`
- `POST /catalog/courses`
- `PUT /catalog/courses/{id}`
- `DELETE /catalog/courses/{id}`

### 5. Recommendation Service
```
┌─────────────────────────────────────────────────────────────┐
│              Recommendation Service                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   ML Model  │ │  Inference  │ │  Ranking    │          │
│  │   Loading   │ │   Engine    │ │   Engine    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Batch      │ │  Real-time  │ │  Model      │          │
│  │  Processing │ │  Inference  │ │  Updates    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                recommendation_db                           │
│  - model_versions (id, version, path, created_at)         │
│  - embeddings (id, entity_type, entity_id, embedding)     │
│  - inference_logs (id, user_id, request, response, time)  │
│  - model_metrics (id, version, metric_name, value, date)  │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Load và quản lý ML models
- Online inference cho recommendations
- Ranking và scoring algorithms
- Model versioning và updates
- Performance monitoring

**API Endpoints:**
- `POST /recommendations/generate`
- `GET /recommendations/{user_id}`
- `POST /recommendations/batch`
- `GET /recommendations/models`
- `POST /recommendations/models/update`

### 6. Study Plan Service
```
┌─────────────────────────────────────────────────────────────┐
│               Study Plan Service                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Create Plan  │ │ Update Plan │ │ Delete Plan │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Time Slot    │ │ Conflict    │ │ Schedule    │          │
│  │Validation   │ │ Detection   │ │ Management  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                 studyplan_db                               │
│  - study_plans (id, user_id, created_at, updated_at)      │
│  - plan_items (id, plan_id, item_type, item_id, time_slot)│
│  - time_slots (id, plan_id, day, start_time, end_time)    │
│  - conflicts (id, plan_id, conflicting_items, resolved)   │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Quản lý kế hoạch học tập
- Validation thời gian học
- Phát hiện xung đột lịch
- Quản lý schedule

**API Endpoints:**
- `POST /study-plans`
- `GET /study-plans/{user_id}`
- `PUT /study-plans/{plan_id}`
- `DELETE /study-plans/{plan_id}`
- `POST /study-plans/{plan_id}/items`
- `GET /study-plans/{plan_id}/conflicts`

### 7. Feedback Service
```
┌─────────────────────────────────────────────────────────────┐
│                Feedback Service                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Submit       │ │ Get         │ │ Analytics   │          │
│  │Feedback     │ │ Feedback    │ │ Dashboard   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Rating       │ │ Feedback    │ │ Report      │          │
│  │Management   │ │ Aggregation │ │ Generation  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  feedback_db                               │
│  - feedbacks (id, user_id, type, content, rating, date)   │
│  - ratings (id, entity_type, entity_id, user_id, rating)  │
│  - feedback_analytics (id, date, total_feedback, avg_rating)│
│  - reports (id, type, data, generated_at)                 │
└─────────────────────────────────────────────────────────────┘
```

**Chức năng:**
- Thu thập feedback từ người dùng
- Quản lý rating system
- Phân tích và báo cáo feedback
- Dashboard analytics

**API Endpoints:**
- `POST /feedback`
- `GET /feedback/{user_id}`
- `GET /feedback/analytics`
- `POST /feedback/ratings`
- `GET /feedback/reports`

## 🗄️ Database Design

### Database Separation Strategy

#### 1. auth_db
```sql
-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Login logs table
CREATE TABLE login_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 2. profile_db
```sql
-- Profiles table
CREATE TABLE profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    school VARCHAR(200),
    current_grade VARCHAR(50),
    favorite_subjects TEXT,
    learning_goals TEXT,
    preferred_learning_method VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Profile history table
CREATE TABLE profile_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    profile_id INT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- Preferences table
CREATE TABLE preferences (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    learning_method VARCHAR(200),
    subjects TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### 3. catalog_db
```sql
-- Courses table
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade_level VARCHAR(20) NOT NULL,
    teaching_method VARCHAR(20),
    teaching_time VARCHAR(100),
    location VARCHAR(200),
    cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tutors table
CREATE TABLE tutors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    specialized_grade VARCHAR(20),
    teaching_method VARCHAR(20),
    teaching_time VARCHAR(200),
    experience INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Materials table
CREATE TABLE materials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    grade_level VARCHAR(20),
    material_type VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Search index table
CREATE TABLE search_index (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type ENUM('course', 'tutor', 'material') NOT NULL,
    entity_id INT NOT NULL,
    search_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_id),
    FULLTEXT idx_search (search_text)
);
```

#### 4. studyplan_db
```sql
-- Study plans table
CREATE TABLE study_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Plan items table
CREATE TABLE plan_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plan_id INT NOT NULL,
    item_type ENUM('course', 'tutor', 'material') NOT NULL,
    item_id INT NOT NULL,
    time_slot VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
);

-- Time slots table
CREATE TABLE time_slots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plan_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
);

-- Conflicts table
CREATE TABLE conflicts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plan_id INT NOT NULL,
    conflicting_items TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
);
```

#### 5. feedback_db
```sql
-- Feedbacks table
CREATE TABLE feedbacks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ratings table
CREATE TABLE ratings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type ENUM('course', 'tutor', 'material') NOT NULL,
    entity_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_rating (entity_type, entity_id, user_id)
);

-- Feedback analytics table
CREATE TABLE feedback_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL,
    total_feedback INT DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date)
);
```

#### 6. recommendation_db
```sql
-- Model versions table
CREATE TABLE model_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version VARCHAR(50) NOT NULL,
    model_path VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Embeddings table
CREATE TABLE embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type ENUM('course', 'tutor', 'material') NOT NULL,
    entity_id INT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_embedding (entity_type, entity_id)
);

-- Inference logs table
CREATE TABLE inference_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    request_data JSON,
    response_data JSON,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model metrics table
CREATE TABLE model_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚖️ Load Balancing & Caching Strategy

### 1. Load Balancing với NGINX

#### NGINX Configuration
```nginx
upstream auth_service {
    least_conn;
    server auth-service-1:8001;
    server auth-service-2:8001;
    server auth-service-3:8001;
}

upstream profile_service {
    least_conn;
    server profile-service-1:8002;
    server profile-service-2:8002;
    server profile-service-3:8002;
}

upstream catalog_service {
    least_conn;
    server catalog-service-1:8003;
    server catalog-service-2:8003;
    server catalog-service-3:8003;
}

upstream recommendation_service {
    least_conn;
    server recommendation-service-1:8004;
    server recommendation-service-2:8004;
    server recommendation-service-3:8004;
}

upstream studyplan_service {
    least_conn;
    server studyplan-service-1:8005;
    server studyplan-service-2:8005;
    server studyplan-service-3:8005;
}

upstream feedback_service {
    least_conn;
    server feedback-service-1:8006;
    server feedback-service-2:8006;
    server feedback-service-3:8006;
}

server {
    listen 80;
    server_name api.studyplan.com;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Auth service routes
    location /api/auth/ {
        proxy_pass http://auth_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Profile service routes
    location /api/profiles/ {
        proxy_pass http://profile_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Catalog service routes
    location /api/catalog/ {
        proxy_pass http://catalog_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Recommendation service routes
    location /api/recommendations/ {
        proxy_pass http://recommendation_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Study plan service routes
    location /api/study-plans/ {
        proxy_pass http://studyplan_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Feedback service routes
    location /api/feedback/ {
        proxy_pass http://feedback_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Caching Strategy với Redis

#### Cache Keys Design
```python
# Cache key patterns
CACHE_PATTERNS = {
    'user_profile': 'profile:{user_id}',
    'catalog_courses': 'catalog:courses:{filters_hash}',
    'catalog_tutors': 'catalog:tutors:{filters_hash}',
    'catalog_materials': 'catalog:materials:{filters_hash}',
    'recommendations': 'recommendations:{user_id}:{profile_hash}',
    'study_plan': 'study_plan:{user_id}',
    'feedback_analytics': 'feedback:analytics:{date}',
    'search_results': 'search:{query_hash}:{filters_hash}'
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    'user_profile': 3600,        # 1 hour
    'catalog_courses': 1800,     # 30 minutes
    'catalog_tutors': 1800,      # 30 minutes
    'catalog_materials': 1800,   # 30 minutes
    'recommendations': 1800,     # 30 minutes
    'study_plan': 300,           # 5 minutes
    'feedback_analytics': 3600,  # 1 hour
    'search_results': 900        # 15 minutes
}
```

#### Cache Implementation
```python
import redis
import json
import hashlib
from typing import Any, Optional

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            serialized_value = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            return self.redis_client.delete(*keys) if keys else 0
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0
    
    def generate_cache_key(self, pattern: str, **kwargs) -> str:
        """Generate cache key from pattern and parameters"""
        return pattern.format(**kwargs)
    
    def generate_filters_hash(self, filters: dict) -> str:
        """Generate hash for filters to use in cache key"""
        filters_str = json.dumps(filters, sort_keys=True)
        return hashlib.md5(filters_str.encode()).hexdigest()[:8]

# Usage example
cache = CacheManager()

# Cache user profile
def get_user_profile(user_id: int):
    cache_key = cache.generate_cache_key('profile:{user_id}', user_id=user_id)
    
    # Try to get from cache first
    cached_profile = cache.get(cache_key)
    if cached_profile:
        return cached_profile
    
    # If not in cache, get from database
    profile = database.get_profile(user_id)
    
    # Store in cache
    cache.set(cache_key, profile, ttl=3600)
    
    return profile

# Cache catalog with filters
def get_catalog_courses(filters: dict):
    filters_hash = cache.generate_filters_hash(filters)
    cache_key = cache.generate_cache_key(
        'catalog:courses:{filters_hash}', 
        filters_hash=filters_hash
    )
    
    cached_courses = cache.get(cache_key)
    if cached_courses:
        return cached_courses
    
    courses = database.get_courses(filters)
    cache.set(cache_key, courses, ttl=1800)
    
    return courses
```

#### Cache Invalidation Strategy
```python
class CacheInvalidationManager:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def invalidate_user_profile(self, user_id: int):
        """Invalidate user profile cache"""
        pattern = f"profile:{user_id}"
        self.cache.delete(pattern)
    
    def invalidate_catalog(self, entity_type: str = None):
        """Invalidate catalog cache"""
        if entity_type:
            pattern = f"catalog:{entity_type}:*"
        else:
            pattern = "catalog:*"
        self.cache.invalidate_pattern(pattern)
    
    def invalidate_recommendations(self, user_id: int = None):
        """Invalidate recommendations cache"""
        if user_id:
            pattern = f"recommendations:{user_id}:*"
        else:
            pattern = "recommendations:*"
        self.cache.invalidate_pattern(pattern)
    
    def invalidate_study_plan(self, user_id: int):
        """Invalidate study plan cache"""
        pattern = f"study_plan:{user_id}"
        self.cache.delete(pattern)
    
    def invalidate_feedback_analytics(self):
        """Invalidate feedback analytics cache"""
        pattern = "feedback:analytics:*"
        self.cache.invalidate_pattern(pattern)
```

## 🚀 Migration Plan

### Phase 1: Infrastructure Setup (Week 1-2)
1. **Setup Docker Environment**
   - Tạo Docker Compose cho microservices
   - Setup NGINX load balancer
   - Setup Redis cache
   - Setup monitoring (Prometheus + Grafana)

2. **Database Migration**
   - Tạo các database riêng biệt
   - Migrate dữ liệu từ monolith database
   - Setup database replication và backup

### Phase 2: Core Services Development (Week 3-6)
1. **Auth Service** (Week 3)
   - Implement JWT authentication
   - User registration/login
   - Password reset functionality
   - Session management

2. **Profile Service** (Week 4)
   - User profile management
   - Profile validation
   - Profile history tracking

3. **Catalog Service** (Week 5)
   - Course/Tutor/Material management
   - Search and filtering
   - Pagination
   - Data validation

4. **Recommendation Service** (Week 6)
   - ML model integration
   - Online inference
   - Model versioning
   - Performance monitoring

### Phase 3: Business Services (Week 7-8)
1. **Study Plan Service** (Week 7)
   - Study plan management
   - Time slot validation
   - Conflict detection
   - Schedule management

2. **Feedback Service** (Week 8)
   - Feedback collection
   - Rating system
   - Analytics dashboard
   - Report generation

### Phase 4: Integration & Testing (Week 9-10)
1. **API Gateway Integration**
   - Route configuration
   - JWT verification
   - Request/response transformation
   - Rate limiting

2. **Load Balancing & Caching**
   - NGINX configuration
   - Redis cache implementation
   - Cache invalidation strategy
   - Performance optimization

3. **Testing & Monitoring**
   - Unit testing
   - Integration testing
   - Load testing
   - Monitoring setup

### Phase 5: Deployment & Migration (Week 11-12)
1. **Production Deployment**
   - Blue-green deployment
   - Database migration
   - Service discovery
   - Health checks

2. **Data Migration**
   - Migrate existing data
   - Data validation
   - Rollback plan
   - Performance verification

3. **Go-Live & Monitoring**
   - Production monitoring
   - Performance metrics
   - Error tracking
   - User feedback

## 📊 Monitoring & Observability

### 1. Metrics Collection
```yaml
# Prometheus configuration
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
  
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8001']
  
  - job_name: 'profile-service'
    static_configs:
      - targets: ['profile-service:8002']
  
  - job_name: 'catalog-service'
    static_configs:
      - targets: ['catalog-service:8003']
  
  - job_name: 'recommendation-service'
    static_configs:
      - targets: ['recommendation-service:8004']
  
  - job_name: 'studyplan-service'
    static_configs:
      - targets: ['studyplan-service:8005']
  
  - job_name: 'feedback-service'
    static_configs:
      - targets: ['feedback-service:8006']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### 2. Health Checks
```python
# Health check implementation for each service
from flask import Flask, jsonify
import redis
import mysql.connector

app = Flask(__name__)

@app.route('/health')
def health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {}
    }
    
    # Check database connection
    try:
        db_connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        health_status['services']['database'] = 'healthy'
        db_connection.close()
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(os.getenv('REDIS_URL'))
        redis_client.ping()
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
```

### 3. Logging Strategy
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        
        # Create handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_request(self, method: str, endpoint: str, user_id: int = None, 
                   status_code: int = None, duration_ms: float = None):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': 'INFO',
            'event': 'request',
            'method': method,
            'endpoint': endpoint,
            'user_id': user_id,
            'status_code': status_code,
            'duration_ms': duration_ms
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error: str, user_id: int = None, 
                  request_id: str = None, stack_trace: str = None):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': 'ERROR',
            'event': 'error',
            'error': error,
            'user_id': user_id,
            'request_id': request_id,
            'stack_trace': stack_trace
        }
        self.logger.error(json.dumps(log_data))
    
    def log_business_event(self, event: str, user_id: int = None, 
                          data: dict = None):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': 'INFO',
            'event': event,
            'user_id': user_id,
            'data': data
        }
        self.logger.info(json.dumps(log_data))
```

## 🔧 Technology Stack

### Backend Services
- **Framework**: Flask (Python 3.10+)
- **Database**: MySQL 8.0
- **Cache**: Redis 7.0
- **ML Framework**: TensorFlow 2.15.0
- **Authentication**: JWT (PyJWT)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Load Balancer**: NGINX
- **Service Discovery**: Consul (optional)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Development Tools
- **API Documentation**: Swagger/OpenAPI
- **Testing**: pytest, Postman
- **CI/CD**: GitHub Actions
- **Code Quality**: Black, Flake8, MyPy

## 📈 Expected Benefits

### 1. Scalability
- **Independent Scaling**: Mỗi service có thể scale riêng biệt
- **Resource Optimization**: Phân bổ tài nguyên theo nhu cầu thực tế
- **Load Distribution**: Phân tải đều giữa các instances

### 2. Reliability
- **Fault Isolation**: Lỗi ở 1 service không ảnh hưởng toàn hệ thống
- **High Availability**: Multiple instances cho mỗi service
- **Graceful Degradation**: Hệ thống vẫn hoạt động khi 1 service down

### 3. Maintainability
- **Code Organization**: Code được tổ chức theo domain
- **Independent Deployment**: Deploy từng service riêng biệt
- **Technology Diversity**: Có thể sử dụng công nghệ khác nhau cho từng service

### 4. Performance
- **Caching**: Giảm tải database với Redis cache
- **Load Balancing**: Phân tải request hiệu quả
- **Database Optimization**: Mỗi service có database riêng

## 🎯 Success Metrics

### Performance Metrics
- **Response Time**: < 200ms cho 95% requests
- **Throughput**: > 1000 requests/second
- **Availability**: 99.9% uptime
- **Cache Hit Rate**: > 80%

### Business Metrics
- **User Satisfaction**: > 4.5/5 rating
- **System Reliability**: < 0.1% error rate
- **Development Velocity**: 50% faster feature delivery
- **Operational Efficiency**: 30% reduction in maintenance time

## 🚨 Risk Mitigation

### 1. Technical Risks
- **Data Consistency**: Implement eventual consistency patterns
- **Service Dependencies**: Circuit breaker pattern
- **Database Migration**: Blue-green deployment
- **Performance Degradation**: Load testing và monitoring

### 2. Operational Risks
- **Deployment Complexity**: Automated CI/CD pipeline
- **Monitoring Overhead**: Centralized logging và monitoring
- **Team Coordination**: Clear communication protocols
- **Rollback Strategy**: Automated rollback mechanisms

## 📝 Next Steps

1. **Immediate Actions** (Week 1)
   - Setup development environment
   - Create project structure
   - Setup Docker containers
   - Design API contracts

2. **Short-term Goals** (Month 1)
   - Complete Phase 1 & 2
   - Implement core services
   - Setup monitoring
   - Begin testing

3. **Medium-term Goals** (Month 2-3)
   - Complete all phases
   - Production deployment
   - Performance optimization
   - User acceptance testing

4. **Long-term Goals** (Month 4+)
   - Continuous improvement
   - Feature enhancements
   - Performance monitoring
   - Team training

---

*Tài liệu này sẽ được cập nhật thường xuyên trong quá trình migration. Mọi thay đổi sẽ được ghi lại trong changelog.*
