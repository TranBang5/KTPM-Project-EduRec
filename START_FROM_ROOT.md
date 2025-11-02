# ✅ Chạy Docker từ Folder Root

Hệ thống đã được cấu hình để **chạy Docker Compose từ folder root** của project.

## 📍 Vị trí Files

- ✅ **`docker-compose.yml`** - Ở **ROOT folder** (chạy từ đây)
- ✅ **`start.ps1`** / **`start.sh`** - Scripts start ở ROOT
- ✅ **`env.example`** - Template config ở ROOT

## 🚀 Cách chạy

### Từ folder root:

```bash
# Windows PowerShell
.\start.ps1

# Linux/Mac hoặc Git Bash
./start.sh

# Hoặc trực tiếp
docker-compose up -d --build
```

### Kiểm tra:

```bash
# Check services
docker-compose ps

# Check health
curl http://localhost:5000/health
```

## 📊 Docker Compose ở Root

File `docker-compose.yml` ở root có:
- ✅ Database service (MySQL)
- ✅ Tất cả 7 microservices
- ✅ Đường dẫn đúng: `./microservices/service_name`
- ✅ Volumes đúng: `./models`, `./data`, etc.

## 🔍 So sánh

| File | Vị trí | Mục đích |
|------|--------|----------|
| `docker-compose.yml` | **ROOT** | ✅ **Dùng cái này** |
| `microservices/docker-compose.yml` | microservices/ | ⚠️ Legacy (có thể xóa) |

## ⚠️ Lưu ý

- **Luôn chạy từ root**: `docker-compose` commands từ folder root
- **Paths đã được fix**: Tất cả paths trong docker-compose.yml đã đúng cho root
- **Volumes**: Mount từ root (`./models`, `./data`)

## 🎯 Quick Commands

```bash
# Từ ROOT folder
docker-compose up -d --build    # Start all
docker-compose ps               # Status
docker-compose logs -f          # Logs
docker-compose down             # Stop
```

---

**✅ System ready to run from root!**
