# Session 9: ML Model Monitoring with Automatic Drift Detection

This session demonstrates a complete MLOps monitoring stack with **automatic drift detection**, combining metrics, logs, and model performance monitoring in a production-ready setup.

## 📋 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Module Descriptions](#module-descriptions)
- [Prerequisites](#prerequisites)
- [Step-by-Step Setup](#step-by-step-setup)
- [Usage Guide](#usage-guide)
- [Accessing Services](#accessing-services)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

This setup includes 6 interconnected services:

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│   ML Service    │─────▶│  Prometheus  │─────▶│   Grafana   │
│   (FastAPI)     │      │   (Metrics)  │      │ (Dashboard) │
└─────────────────┘      └──────────────┘      └─────────────┘
         │                                              ▲
         │                                              │
         ▼                                              │
┌─────────────────┐      ┌──────────────┐               │
│  Drift Reports  │      │     Loki     │───────────────┘
│  (Evidently)    │      │    (Logs)    │
└─────────────────┘      └──────────────┘
         ▲                       ▲
         │                       │
         │               ┌───────────────┐
         │               │   Promtail    │
         │               │(Log Collector)│
         │               └───────────────┘
         │
┌─────────────────┐
│  Report Viewer  │
│    (Nginx)      │
└─────────────────┘
```

---

## 📦 Module Descriptions

### 1. **main.py** - ML Service (FastAPI)
**Role**: Core prediction service with automatic drift detection.

**Features**:
- Serves an Iris classification model (Random Forest)
- Exposes `/predict` endpoint for predictions
- **Automatic drift detection**: Generates reports every 5 minutes
- Collects production data for monitoring (rolling window of 500 samples)
- Exposes `/metrics` endpoint for Prometheus
- Includes health and monitoring status endpoints

**Key Endpoints**:
- `POST /predict` - Make predictions
- `GET /health` - Health check
- `GET /monitor/status` - Check drift monitoring status
- `POST /monitor/trigger_now` - Manually trigger drift detection
- `GET /monitor/generate_report` - Generate manual report (optional)
- `GET /metrics` - Prometheus metrics

**Automatic Features**:
- Background scheduler runs drift detection every 5 minutes
- Automatically generates Evidently reports when enough data is collected
- Saves reports with timestamps for tracking over time

---

### 2. **docker-compose.yaml** - Infrastructure Orchestration
**Role**: Defines and manages all services in the monitoring stack.

**Services Defined**:
- **ml_service**: The ML prediction service (port 8000)
- **prometheus**: Metrics collection and storage (port 9090)
- **loki**: Log aggregation system (port 3100)
- **promtail**: Log collector that sends logs to Loki
- **grafana**: Visualization dashboard (port 3000)
- **report_server**: Nginx server for viewing Evidently reports (port 8080)

**Key Features**:
- All services connected via `monitoring` network
- Persistent volumes for Grafana and Loki data
- Shared volume for drift reports between ML service and report viewer
- Automatic log collection from Docker containers

---

### 3. **grafana_setup.py** - Automatic Dashboard Configuration
**Role**: Automatically configures Grafana with datasources and dashboards.

**What it does**:
1. Waits for Grafana to be ready
2. Configures Prometheus datasource (for metrics)
3. Configures Loki datasource (for logs)
4. Creates "ML Service Health" dashboard with:
   - Requests per Second (RPS) chart
   - 99th Percentile Latency chart
   - Total Predictions counter
   - Real-time ML service logs panel

**Benefits**: No manual Grafana configuration needed!

---

### 4. **simulator.py** - Traffic Generation Tool
**Role**: Generates realistic and drifted traffic for testing.

**Functionality**:
- **Normal Traffic**: Generates data similar to Iris dataset (50 requests)
- **Drifted Traffic**: Generates intentionally drifted data (50 requests)
  - Higher sepal length values (+2.5)
  - Lower sepal width values (-1.0)
  - Higher petal length values (+3.0)
- Random delays between requests to simulate real traffic

**Use Case**: Perfect for testing drift detection and monitoring dashboards.

---

### 5. **dockerfile** - ML Service Container
**Role**: Defines how to build the ML service Docker image.

**Contents**:
- Uses Python 3.12 slim image
- Installs dependencies from requirements.txt
- Copies main.py into container
- Creates reports directory
- Runs uvicorn server on port 8000

---

### 6. **prometheus/prometheus.yml** - Metrics Configuration
**Role**: Configures Prometheus to scrape metrics from ML service.

**Configuration**:
- Scrapes ML service every 5 seconds
- Targets: `ml_service:8000/metrics`
- Fast scraping for demo purposes

---

### 7. **promtail/promtail-config.yaml** - Log Collection Configuration
**Role**: Configures Promtail to collect Docker container logs and send to Loki.

**Features**:
- Auto-discovers Docker containers
- Extracts container metadata (name, ID, stream)
- Parses JSON logs
- Extracts log levels (INFO, DEBUG, WARNING, ERROR)
- Adds labels for easy filtering in Grafana

---

## ✅ Prerequisites

### Required Software:
- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python** (v3.12+)

### Verify Installation:
```bash
docker --version
docker-compose --version
python --version
```

---

## 🚀 Step-by-Step Setup

### Step 1: Navigate to Session 9 Directory
```bash
cd /Users/danhmac/Documents/mlops-course-solutions/scripts/session_9
```

### Step 2: Build and Start All Services
```bash
docker-compose up --build -d
```

**What happens**:
- Builds the ML service Docker image
- Pulls required images (Prometheus, Loki, Promtail, Grafana, Nginx)
- Starts all 6 services
- Creates monitoring network and persistent volumes

**Expected output**:
```
✅ Container ml_service created
✅ Container prometheus created
✅ Container loki created
✅ Container promtail created
✅ Container grafana created
✅ Container report_viewer created
```

### Step 3: Verify Services are Running
```bash
docker-compose ps
```

**Expected output**: All services should show "Up" status.

### Step 4: Wait for Services to Initialize (30-60 seconds)
```bash
# Check ML service logs
docker-compose logs ml_service

# Look for these lines:
# ✅ Background scheduler started successfully
# ✅ Automatic drift detection scheduler started
```

### Step 5: Configure Grafana (Automatic Setup)
```bash
# Install dependencies if not already installed
pip install requests

# Run the setup script
python grafana_setup.py
```

**Expected output**:
```
Waiting for Grafana to be ready...
Configuring Prometheus Datasource...
Prometheus Datasource: 200
Configuring Loki Datasource...
Loki Datasource: 200
Creating Monitoring Dashboard...
Dashboard Status: 200
Grafana setup complete!
```

**Note**: Login with `admin/admin` if prompted.

### Step 6: Generate Traffic with Simulator
```bash
python simulator.py
```

**What it does**:
1. Sends 50 normal prediction requests
2. Sends 50 drifted prediction requests
3. Displays progress in real-time

**Expected output**:
```
[1/50] normal request sent. Status: 200
[2/50] normal request sent. Status: 200
...
[1/50] drift request sent. Status: 200
...
Simulation Complete!
```

### Step 7: Wait for Automatic Drift Detection (or Trigger Manually)

**Option A: Wait for Automatic Detection (Recommended)**
- Drift reports are automatically generated every 5 minutes
- Check status: http://localhost:8000/monitor/status
- View latest report: http://localhost:8080/drift_report_latest.html

**Option B: Trigger Immediately (For Testing)**
```bash
curl -X POST http://localhost:8000/monitor/trigger_now
```

---

## 📊 Usage Guide

### Making Predictions

**Using curl**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sepal length (cm)": 5.1,
    "sepal width (cm)": 3.5,
    "petal length (cm)": 1.4,
    "petal width (cm)": 0.2
  }'
```

**Expected response**:
```json
{
  "class": "setosa",
  "class_id": 0
}
```

**Using Python**:
```python
import requests

data = {
    "sepal length (cm)": 5.1,
    "sepal width (cm)": 3.5,
    "petal length (cm)": 1.4,
    "petal width (cm)": 0.2
}

response = requests.post("http://localhost:8000/predict", json=data)
print(response.json())
```

---

### Monitoring Status

**Check drift monitoring status**:
```bash
curl http://localhost:8000/monitor/status
```

**Response includes**:
- Automatic detection status (enabled/disabled)
- Next scheduled run time
- Current data points collected
- Recent reports list
- Latest report URL

---

### Manual Drift Report Generation

**Trigger immediate drift detection**:
```bash
curl -X POST http://localhost:8000/monitor/trigger_now
```

**Generate manual report (alternative)**:
```bash
curl http://localhost:8000/monitor/generate_report
```

---

## 🌐 Accessing Services

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **ML Service** | http://localhost:8000 | - | Prediction API |
| **ML Service Docs** | http://localhost:8000/docs | - | Interactive API documentation |
| **Prometheus** | http://localhost:9090 | - | Metrics database and query UI |
| **Grafana** | http://localhost:3000 | admin / admin | Monitoring dashboards |
| **Loki** | http://localhost:3100 | - | Log aggregation (internal) |
| **Drift Reports** | http://localhost:8080 | - | Evidently HTML reports |

---

## 📈 Using Grafana Dashboard

1. **Access Grafana**: http://localhost:3000
2. **Login**: admin / admin (change password if prompted)
3. **View Dashboard**: Click "ML Service Health" dashboard

**Dashboard Panels**:
- **Requests per Second**: Real-time request rate per endpoint
- **99th Percentile Latency**: Response time performance
- **Total Predictions**: Cumulative prediction count
- **ML Service Logs**: Filtered logs with level highlighting

**Useful Queries**:
- Filter logs by level: `{container="ml_service"} |= "INFO"`
- Search for drift: `{container="ml_service"} |= "drift"`
- Error logs only: `{container="ml_service"} |= "ERROR"`

---

## 📊 Viewing Drift Reports

### Latest Report (Always Available):
http://localhost:8080/drift_report_latest.html

### All Reports:
http://localhost:8080/

**Report Naming Convention**:
- `drift_report_YYYYMMDD_HHMMSS.html` - Automatically generated
- `drift_report_manual_YYYYMMDD_HHMMSS.html` - Manually triggered
- `drift_report_latest.html` - Always points to most recent

**Report Contents**:
- Dataset drift summary
- Feature-by-feature drift analysis
- Distribution comparisons (reference vs current)
- Statistical tests (Kolmogorov-Smirnov, etc.)
- Drift detection alerts

---

## 🛑 Stopping Services

**Stop all services**:
```bash
docker-compose down
```

**Stop and remove volumes (clean slate)**:
```bash
docker-compose down -v
```

**Stop but keep data**:
```bash
docker-compose stop
```

**Restart services**:
```bash
docker-compose restart
```

---

## 🔧 Troubleshooting

### Issue: Services won't start
**Solution**:
```bash
# Check for port conflicts
lsof -i :8000  # ML service
lsof -i :3000  # Grafana
lsof -i :9090  # Prometheus

# Kill conflicting processes or change ports in docker-compose.yaml
```

### Issue: Grafana setup fails
**Solution**:
```bash
# Wait longer for Grafana to start
sleep 30

# Try manual setup
python grafana_setup.py

# Or access Grafana UI and configure manually
# - Add Prometheus datasource: http://prometheus:9090
# - Add Loki datasource: http://loki:3100
```

### Issue: No drift reports generated
**Check**:
1. Enough data collected (minimum 10 samples)?
   ```bash
   curl http://localhost:8000/monitor/status
   ```
2. Run simulator to generate data
   ```bash
   python simulator.py
   ```
3. Trigger manually
   ```bash
   curl -X POST http://localhost:8000/monitor/trigger_now
   ```
4. Check ML service logs
   ```bash
   docker-compose logs ml_service | grep drift
   ```

### Issue: Prometheus not collecting metrics
**Solution**:
```bash
# Check Prometheus targets
# Go to http://localhost:9090/targets
# ml_service should show "UP"

# If DOWN, check ML service health
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Issue: Logs not showing in Grafana
**Solution**:
```bash
# Check Promtail is running
docker-compose ps promtail

# Check Promtail logs
docker-compose logs promtail

# Verify Loki datasource in Grafana
# Dashboards → Explore → Select Loki → Query: {container="ml_service"}
```

### Issue: Reports directory permission denied
**Solution**:
```bash
# Fix permissions
chmod -R 755 reports/

# Or rebuild with proper permissions
docker-compose down -v
docker-compose up --build -d
```

---

## 📝 Key Features

### ✨ Automatic Drift Detection
- **Frequency**: Every 5 minutes (configurable in main.py line 117)
- **Minimum Data**: 10 samples required
- **Report Types**: Timestamped + latest
- **Storage**: Local reports/ directory, shared with Nginx

### 📊 Comprehensive Monitoring
- **Metrics**: Request rate, latency, prediction counts
- **Logs**: Structured logging with levels
- **Dashboards**: Pre-configured Grafana visualizations
- **Alerts**: Can be added to Grafana dashboards

### 🔄 Rolling Data Window
- Stores last 500 predictions
- Automatic memory management
- In-memory storage (use database in production!)

### 🚀 Production-Ready Architecture
- Containerized services
- Service discovery via Docker networking
- Persistent storage for time-series data
- Horizontal scaling ready (increase replicas)

---

## 🎯 Next Steps

### For Development:
1. Add authentication to ML service
2. Implement model versioning
3. Add more drift metrics (concept drift, performance drift)
4. Set up alerting in Grafana

### For Production:
1. Use external database for production data
2. Set up proper secrets management
3. Configure backup for Prometheus and Loki data
4. Add HTTPS/TLS certificates
5. Set up distributed tracing (Jaeger/Zipkin)
6. Implement A/B testing framework

---

## 📚 Additional Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **Loki**: https://grafana.com/docs/loki/
- **Evidently**: https://docs.evidentlyai.com/
- **APScheduler**: https://apscheduler.readthedocs.io/

---

## 🎓 Learning Objectives

By completing this session, you learned:
1. ✅ Setting up production ML monitoring stack
2. ✅ Implementing automatic drift detection
3. ✅ Collecting and visualizing metrics with Prometheus/Grafana
4. ✅ Aggregating logs with Loki/Promtail
5. ✅ Containerizing ML services with Docker
6. ✅ Orchestrating multi-service applications
7. ✅ Generating model performance reports with Evidently

---

**Happy Monitoring! 🎉**
