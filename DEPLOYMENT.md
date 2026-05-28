# Deployment Guide

## 🚀 Deployment Options

### Option 1: Local Docker (Development)

```bash
# Clone repository
git clone <your-repo-url>
cd refund-ai-agent

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access:**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Option 2: Cloud Deployment (AWS, GCP, Azure)

#### AWS ECS + Fargate

```bash
# Create ECR repositories
aws ecr create-repository --repository-name refund-agent-backend
aws ecr create-repository --repository-name refund-agent-frontend

# Build and push images
docker build -f docker/Dockerfile.backend -t refund-agent-backend .
docker tag refund-agent-backend:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/refund-agent-backend:latest
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/refund-agent-backend:latest

# Similar for frontend...

# Create ECS task definitions and services
# (See AWS documentation for detailed setup)
```

#### Google Cloud Run

```bash
# Build images with Cloud Build
gcloud builds submit --config cloudconfig.yaml

# Deploy to Cloud Run
gcloud run deploy refund-agent-backend \
  --image gcr.io/PROJECT-ID/refund-agent-backend:latest \
  --platform managed \
  --region us-central1
```

#### Azure Container Instances

```bash
# Push to Azure Container Registry
az acr build --registry <registry-name> \
  --image refund-agent-backend:latest \
  -f docker/Dockerfile.backend .

# Deploy to Container Instances
az container create \
  --resource-group <group> \
  --name refund-agent-backend \
  --image <registry>.azurecr.io/refund-agent-backend:latest \
  --ports 8000 \
  --cpu 1 --memory 1
```

---

### Option 3: Kubernetes Deployment

#### Create Kubernetes Manifests

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: refund-agent-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: refund-agent-backend
  template:
    metadata:
      labels:
        app: refund-agent-backend
    spec:
      containers:
      - name: backend
        image: refund-agent-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: PYTHONUNBUFFERED
          value: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

```bash
# Deploy to Kubernetes
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Check status
kubectl get pods
kubectl get services
```

---

## 🔐 Security Best Practices

### 1. Environment Variables

Never commit secrets! Use environment variables:

```bash
# .env (never commit this!)
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
SECRET_KEY=random-secret-key-here
JWT_SECRET=random-jwt-secret
```

```python
# Python code
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 2. HTTPS/TLS

```nginx
# nginx.conf (reverse proxy example)
server {
    listen 443 ssl;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

### 3. API Authentication

```python
# Add JWT authentication to FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/refund/process")
async def process_refund(request: RefundRequest, credentials = Depends(security)):
    token = credentials.credentials
    # Verify token
    if not verify_token(token):
        raise HTTPException(status_code=401)
    # ... rest of logic
```

### 4. Database Security

If migrating to production database:

```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)
```

### 5. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/refund/process")
@limiter.limit("100/minute")
async def process_refund(request: RefundRequest):
    # ... logic
```

---

## 📊 Monitoring & Logging

### 1. Application Logging

```python
# Configure logging
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
logging.getLogger().addHandler(handler)
```

### 2. Prometheus Metrics

```python
from prometheus_client import Counter, Histogram
import time

refund_decisions = Counter(
    'refund_decisions_total',
    'Total refund decisions',
    ['decision_type']
)

decision_time = Histogram(
    'refund_decision_time_seconds',
    'Time to make decision'
)

@app.post("/api/refund/process")
def process_refund(request: RefundRequest):
    with decision_time.time():
        result = agent.process_refund_request(...)
        refund_decisions.labels(decision_type=result['decision']).inc()
        return result
```

### 3. ELK Stack Integration

```yaml
# docker-compose.yml (add monitoring services)
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"

logstash:
  image: docker.elastic.co/logstash/logstash:8.0.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

---

## 🗄️ Database Migration

For scaling to production, migrate from JSON to PostgreSQL:

```python
# models.py (SQLAlchemy)
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    account_status = Column(String)
    total_spent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(String, primary_key=True)
    customer_id = Column(String)
    order_date = Column(DateTime)
    purchase_amount = Column(Float)
    is_final_sale = Column(Boolean)
    days_since_purchase = Column(Integer)
    status = Column(String)
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker images
      run: |
        docker build -f docker/Dockerfile.backend -t refund-agent-backend .
        docker build -f docker/Dockerfile.frontend -t refund-agent-frontend .
    
    - name: Push to Docker Hub
      run: |
        docker login -u ${{ secrets.DOCKER_USERNAME }} -p ${{ secrets.DOCKER_PASSWORD }}
        docker push refund-agent-backend:latest
        docker push refund-agent-frontend:latest
    
    - name: Deploy to production
      run: |
        # SSH into server and redeploy
        ssh ${{ secrets.PROD_SERVER }} \
          'cd refund-agent && docker-compose pull && docker-compose up -d'
```

---

## ✅ Production Checklist

- [ ] Enable HTTPS/TLS
- [ ] Set up API authentication (JWT)
- [ ] Configure rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Enable logging (ELK or CloudWatch)
- [ ] Database backup strategy
- [ ] Error tracking (Sentry)
- [ ] Load balancing configured
- [ ] Health checks passing
- [ ] Secrets in environment variables
- [ ] Database migrations tested
- [ ] Disaster recovery plan
- [ ] Documentation updated
- [ ] Performance tested (load testing)
- [ ] Security audit completed

---

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild images
docker-compose up -d --build

# Clear volumes (⚠️ loses data)
docker-compose down -v
docker-compose up -d
```

### High Memory Usage

```bash
# Limit container resources
docker update --memory 1g refund-agent-api
docker update --memory 1g refund-agent-ui
```

### Database Connection Issues

```bash
# Test connection
docker exec refund-agent-api python -c "import psycopg2; psycopg2.connect('postgresql://user:pass@db:5432/refund_db')"

# Check database logs
docker-compose logs db
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

```bash
# Run multiple backend instances
docker-compose scale backend=3

# Or with Kubernetes
kubectl scale deployment refund-agent-backend --replicas=5
```

### Load Balancing

```nginx
upstream backend {
    server refund-agent-api-1:8000;
    server refund-agent-api-2:8000;
    server refund-agent-api-3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

### Caching

```python
from functools import lru_cache
import redis

cache = redis.Redis(host='localhost', port=6379)

@app.get("/api/customer/{customer_id}")
def get_customer(customer_id: str):
    cached = cache.get(f"customer:{customer_id}")
    if cached:
        return json.loads(cached)
    
    customer = db.get_customer(customer_id)
    cache.setex(f"customer:{customer_id}", 3600, json.dumps(customer))
    return customer
```

---

**Last Updated**: March 2024
