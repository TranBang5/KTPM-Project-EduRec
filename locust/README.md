# Locust Load Testing for EduRec Microservices System

This directory contains the Locust load testing setup for measuring performance of the EduRec Microservices architecture.

## Setup

### Using Docker Compose (Recommended)

The Locust service is included in the main `docker-compose.yml` file.

1. **Start the system with Locust:**
   ```bash
   docker-compose up -d
   ```

2. **Access Locust Web UI:**
   - Open browser: `http://localhost:8089`
   - Default settings:
     - Number of users: Start with 10
     - Spawn rate: 2 users/second
     - Host: `http://api-gateway:5000`

3. **Run tests:**
   - Click "Start swarming" to begin testing
   - Monitor real-time statistics in the web UI

### Manual Setup

If you want to run Locust manually:

```bash
# Install Locust
pip install locust

# Run Locust
locust --host=http://localhost:5000 -f locustfile.py
```

## Test Scenarios

### 1. EduRecUser (Main User Class)
- **Tasks:**
  - Registration and Login
  - Health checks (3x weight)
  - Get recommendations (5x weight)
  - Get study plan (4x weight)
  - Get profile (2x weight)
  - Get feedback (2x weight)
  - Get catalog items (1x each)

- **Usage:** General system load testing

### 2. AuthSequentialTaskSet
- **Flow:** Complete authentication flow
  - Register → Login → Get Profile
  
- **Usage:** Test authentication performance

### 3. StudyPlanTaskSet
- **Flow:** Complete study plan operations
  - Create study plan → Add item → Get study plan → Get schedule
  
- **Usage:** Test study plan performance

### 4. ApiGatewayUser
- **Tasks:**
  - API Gateway health checks
  - Service health monitoring
  
- **Usage:** Test API Gateway overhead

### 5. RecommendationUser
- **Tasks:**
  - Generate recommendations (10x weight)
  - Get recommendations (3x weight)
  
- **Usage:** Test recommendation service performance

## Running Tests

### Basic Test
```bash
# Start Locust via Docker Compose
docker-compose up -d locust

# Access Web UI
open http://localhost:8089
```

### CLI Test (Headless Mode)
```bash
# Run without web UI
docker-compose run --rm locust locust --host=http://api-gateway:5000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html report.html
```

### Distributed Test (Multiple Workers)
```bash
# Start master
docker-compose up -d locust

# Start worker (in separate terminal)
docker run --rm -it --network edurec-student-study-plan-recommendation-system_microservices-network \
  -v $(pwd)/locustfile.py:/mnt/locust/locustfile.py \
  locustio/locust \
  locust --master-host=locust_master --worker
```

## Test Configuration

### Running Performance Tests

1. **Using Script (Recommended):**
   ```bash
   python locust/compare_performance.py
   ```
   Select from predefined configurations or create a custom one.

2. **Direct CLI Test:**
   ```bash
   # Host: http://api-gateway:5000
   docker-compose run --rm locust locust --host=http://api-gateway:5000 \
     --users 100 --spawn-rate 10 --run-time 5m --headless --html report.html
   ```

## Metrics to Monitor

### Response Time
- **Average:** Overall average response time
- **P50:** Median response time
- **P95:** 95th percentile (important for SLA)
- **P99:** 99th percentile (worst-case scenarios)

### Throughput
- **RPS:** Requests per second
- **Total Requests:** Total number of requests

### Error Rate
- **Failures:** Number of failed requests
- **Failure %:** Percentage of failed requests

### Resource Usage
Monitor Docker containers during tests:
```bash
docker stats
```

## Performance Comparison Script

See `compare_performance.py` for automated comparison between architectures.

## Best Practices

1. **Start Small:** Begin with 10 users, gradually increase
2. **Warm-up:** Allow system to stabilize before measuring
3. **Multiple Runs:** Run tests multiple times for consistency
4. **Monitor Resources:** Watch CPU, memory, and network usage
5. **Realistic Scenarios:** Use task weights that match real usage patterns

## Troubleshooting

### Locust can't connect to API Gateway
- Ensure API Gateway is running: `docker-compose ps`
- Check network: `docker network ls`
- Verify host URL in Locust UI

### High error rates
- Check service logs: `docker-compose logs api-gateway`
- Reduce spawn rate or user count
- Ensure database is healthy

### Slow response times
- Check resource usage: `docker stats`
- Verify services are healthy: `curl http://localhost:5000/health`
- Consider scaling services

## Reports

Generated reports are saved as HTML files. Compare reports:
- `microservices_report.html`
- `monolith_report.html`

Open in browser to view detailed statistics and charts.

