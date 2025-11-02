# Báo cáo các file code đã outdated và không còn được sử dụng

## 📋 Tóm tắt

Sau khi migration sang Microservices architecture, một số file đã không còn được sử dụng hoặc đã outdated.

## 🔴 Files cần xem xét xóa (Không còn được sử dụng)

### 1. **Migration Scripts (Đã hoàn thành migration)**

#### `cleanup_to_microservices.py`
- **Mục đích ban đầu:** Script tự động cleanup và migration sang microservices
- **Trạng thái:** ✅ Migration đã hoàn thành
- **Sử dụng hiện tại:** Không còn được sử dụng
- **Khuyến nghị:** Có thể xóa hoặc di chuyển vào thư mục `archive/` để tham khảo

#### `migrate_data.py`
- **Mục đích ban đầu:** Script migration dữ liệu
- **Trạng thái:** File rỗng hoặc gần như rỗng
- **Sử dụng hiện tại:** Không được sử dụng
- **Khuyến nghị:** ⚠️ **CÓ THỂ XÓA**

#### `microservices/run_migration.py`
- **Mục đích ban đầu:** Script tự động migration
- **Trạng thái:** ✅ Migration đã hoàn thành
- **Sử dụng hiện tại:** Không còn được sử dụng
- **Khuyến nghị:** Có thể xóa hoặc archive

#### `microservices/setup_services.py`
- **Mục đích ban đầu:** Setup services khi chạy local (không Docker)
- **Trạng thái:** ⚠️ Theo `DOCKER_QUICKSTART.md`, không cần nếu dùng Docker
- **Sử dụng hiện tại:** Không được sử dụng trong Docker setup
- **Khuyến nghị:** ⚠️ **CÓ THỂ XÓA** (nếu chỉ dùng Docker) hoặc giữ lại nếu cần chạy local

### 2. **Monolith Application Files**

#### `app.py`
- **Mục đích ban đầu:** Monolith application (1,380+ dòng)
- **Trạng thái:** ⚠️ **OUTDATED** - Đã được thay thế bởi `app_microservices.py`
- **Sử dụng hiện tại:**
  - ❌ Không được sử dụng trong `docker-compose.yml` (dùng `Dockerfile.frontend` với `app_microservices.py`)
  - ⚠️ Vẫn được import bởi `load_data.py`
- **Khuyến nghị:** 
  - Giữ lại nếu `load_data.py` vẫn cần (hoặc update `load_data.py` để không cần `app.py`)
  - Hoặc xóa nếu không cần monolith version nữa

#### `Dockerfile` (root directory)
- **Mục đích ban đầu:** Dockerfile cho monolith application
- **Trạng thái:** ⚠️ **OUTDATED**
- **Sử dụng hiện tại:** ❌ Không được sử dụng trong `docker-compose.yml`
- **Khuyến nghị:** ⚠️ **CÓ THỂ XÓA** hoặc đổi tên thành `Dockerfile.monolith` để archive

### 3. **Migration Files**

#### `migrations/versions/migrate_to_study_plan_items.py`
- **Mục đích ban đầu:** Database migration script
- **Trạng thái:** File rỗng hoặc không có nội dung
- **Sử dụng hiện tại:** Không được sử dụng
- **Khuyến nghị:** ⚠️ **CÓ THỂ XÓA**

### 4. **Duplicate Docker Compose**

#### `microservices/docker-compose.yml`
- **Mục đích ban đầu:** Docker Compose file riêng cho microservices folder
- **Trạng thái:** ⚠️ **OUTDATED** - Có `docker-compose.yml` ở root
- **Sử dụng hiện tại:** ❌ Không được sử dụng (root `docker-compose.yml` là file chính)
- **Khuyến nghị:** ⚠️ **CÓ THỂ XÓA** hoặc kiểm tra xem có khác biệt gì không

## 🟡 Files cần cập nhật (Vẫn được sử dụng nhưng cần chỉnh sửa)

### 1. **`load_data.py`**
- **Vấn đề:** Import từ `app.py` (monolith) thay vì `app_microservices.py`
- **Trạng thái:** ⚠️ Vẫn cần để load data vào database
- **Khuyến nghị:** 
  - Cập nhật để sử dụng models trực tiếp (không cần Flask app context)
  - Hoặc tạo script riêng để load data vào Catalog Service

### 2. **Documentation Files**
- **`QUICK_START.md`**, **`START_FROM_ROOT.md`**, **`ARCHIVE_README.md`**: 
  - Có thể chứa thông tin outdated về `app.py`
  - **Khuyến nghị:** Review và cập nhật nếu cần

## ✅ Files vẫn được sử dụng (KHÔNG xóa)

### Files còn cần thiết:
- ✅ `app_microservices.py` - Frontend application (đang sử dụng)
- ✅ `Dockerfile.frontend` - Frontend Dockerfile (đang sử dụng)
- ✅ `docker-compose.yml` (root) - Main Docker Compose (đang sử dụng)
- ✅ `microservices/**/app.py` - Tất cả service applications (đang sử dụng)
- ✅ `models/` - Models vẫn được sử dụng bởi services
- ✅ `templates/`, `static/` - Frontend templates và static files (đang sử dụng)
- ✅ `locustfile.py` - Locust test file (đang sử dụng)
- ✅ `train_model.py` - Model training script (vẫn cần để train model)

## 📝 Khuyến nghị hành động

### Priority 1: Có thể xóa ngay (An toàn) - ✅ ĐÃ XÓA
1. ✅ `migrate_data.py` (file rỗng) - **ĐÃ XÓA**
2. ✅ `migrations/versions/migrate_to_study_plan_items.py` (file rỗng) - **ĐÃ XÓA**
3. ✅ `microservices/docker-compose.yml` (duplicate) - **ĐÃ XÓA**
4. ✅ `start_frontend.ps1` (file rỗng) - **ĐÃ XÓA**

### Priority 2: Xem xét xóa (Cần kiểm tra) - ✅ ĐÃ XÓA (trừ setup_services.py)
1. ✅ `cleanup_to_microservices.py` - Script migration đã hoàn thành - **ĐÃ XÓA**
2. ✅ `microservices/run_migration.py` - Script migration đã hoàn thành - **ĐÃ XÓA**
3. ⚠️ `microservices/setup_services.py` - **GIỮ LẠI** (theo yêu cầu)
4. ✅ `Dockerfile` (root) - Monolith Dockerfile, không còn dùng - **ĐÃ XÓA**

### Priority 3: Cần cập nhật hoặc quyết định - ✅ ĐÃ CẬP NHẬT & XÓA
1. ✅ `app.py` - Monolith app:
   - **ĐÃ XÓA:** File monolith đã không còn cần thiết sau khi migration sang microservices
   - **Lưu ý:** `load_data.py` đã không còn phụ thuộc vào `app.py`

2. ✅ `load_data.py` - Data loading script:
   - **ĐÃ CẬP NHẬT:** Tạo Flask app instance riêng, không còn import từ `app.py`
   - **Thay đổi:** 
     - Tạo Flask app instance trong chính `load_data.py`
     - Sử dụng `DATABASE_URL` từ environment variables
     - Khởi tạo database connection độc lập

## 🔍 Cách kiểm tra

### Kiểm tra file có được sử dụng:
```bash
# Kiểm tra imports
grep -r "from.*app import\|import.*app" .

# Kiểm tra trong Docker
grep -r "Dockerfile\|app.py" docker-compose.yml

# Kiểm tra scripts
grep -r "cleanup_to_microservices\|run_migration\|setup_services" .
```

## ⚠️ Lưu ý

1. **Backup trước khi xóa:** Tạo backup của các file trước khi xóa
2. **Test sau khi xóa:** Đảm bảo hệ thống vẫn hoạt động sau khi xóa
3. **Git history:** Files đã được track bởi Git, có thể restore nếu cần

