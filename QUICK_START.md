# 🚀 Quick Start Guide

Get the AI Refund Agent running in 5 minutes!

## Option 1: Docker (Recommended - 2 minutes) ⚡

### Prerequisites
- Docker and Docker Compose installed
- Git (optional)

### Steps

```bash
# 1. Navigate to project directory
cd refund-ai-agent

# 2. Start all services with one command
docker-compose up -d

# 3. Wait for services to be ready (20-30 seconds)
# Check status with:
docker-compose ps

# 4. Access the application
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Verify It's Working

```bash
# Test backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"Refund Agent API"}
```

---

## Option 2: Local Development (Python)

### Prerequisites
- Python 3.9+
- pip
- Virtual environment tool (venv)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start server
python -m uvicorn main:app --reload

# Backend runs at: http://localhost:8000
```

### Frontend Setup (New Terminal)

```bash
# 1. Navigate to frontend
cd frontend

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start app
streamlit run app.py

# Frontend runs at: http://localhost:8501
```

---

## 🧪 Test the System

### Using Streamlit UI (Easiest)

1. Open http://localhost:8501 in your browser
2. Choose "Customer Support" tab
3. Enter test data:
   ```
   Customer ID: CUST001
   Order ID: ORD-2024-001
   Reason: Item arrived damaged
   Amount: 300 (optional)
   ```
4. Click "Submit Refund Request"
5. View the decision and reasoning log

### Admin Dashboard

1. Go to "Admin Dashboard" tab
2. View summary metrics
3. See recent requests
4. Click on requests to view detailed reasoning logs

### Using cURL

```bash
# Test a refund request
curl -X POST http://localhost:8000/api/refund/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "order_id": "ORD-2024-001",
    "reason": "Item arrived damaged",
    "requested_amount": 300
  }'

# Get admin dashboard data
curl http://localhost:8000/api/admin/dashboard

# Get conversation history
curl http://localhost:8000/api/admin/conversation-log?limit=10
```

---

## 📋 Test Scenarios

### ✅ Test 1: Simple Approval
```
Customer: CUST001
Order: ORD-2024-001
Reason: Item damaged
Amount: 300
Result: ✅ APPROVED
```

### ❌ Test 2: Final Sale Item
```
Customer: CUST001
Order: ORD-2024-002 (final sale)
Reason: Don't like it
Result: ❌ DENIED (Final Sale)
```

### ⚠️ Test 3: Large Amount
```
Customer: CUST003
Order: ORD-2024-021
Amount: 1500
Result: ⚠️ ESCALATED (>$500)
```

### ❌ Test 4: Suspended Account
```
Customer: CUST005 (suspended)
Order: ORD-2024-040
Result: ❌ DENIED (Suspended Account)
```

See TEST_SCENARIOS.md for more test cases.

---

## 🛑 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
python -m uvicorn main:app --port 8001 --reload
```

### Frontend can't connect to backend
```bash
# Ensure backend is running
curl http://localhost:8000/health

# In Streamlit, set API URL in sidebar:
# API Server URL: http://localhost:8000
```

### Permission denied errors
```bash
# Make sure you're in the right directory
pwd  # Check current location

# Run with proper Python path
python -m uvicorn main:app --reload
```

### Docker issues
```bash
# Rebuild containers
docker-compose up -d --build

# View detailed logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Reset everything
docker-compose down
docker-compose up -d
```

---

## 📊 Project Structure

```
refund-ai-agent/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── agent.py             # Refund logic
│   ├── tools.py             # Database tools
│   ├── models.py            # Data models
│   └── requirements.txt      # Dependencies
├── frontend/
│   ├── app.py               # Streamlit UI
│   └── requirements.txt      # Dependencies
├── data/
│   ├── customers.json       # Customer data
│   ├── orders.json          # Order data
│   └── refund_policy.txt    # Policy rules
├── docker/
│   ├── Dockerfile.backend   # Backend container
│   └── Dockerfile.frontend  # Frontend container
├── docker-compose.yml       # Orchestration
├── README.md                # Full documentation
├── ARCHITECTURE.md          # System design
├── DEPLOYMENT.md            # Production guide
└── TEST_SCENARIOS.md        # Test cases
```

---

## 🎯 Key Features

✅ **Fully Functional**: Complete refund processing system  
✅ **Containerized**: Single command setup with Docker  
✅ **Reasoning Logs**: Full audit trail of decisions  
✅ **Admin Dashboard**: Monitor all decisions and metrics  
✅ **Policy Enforcement**: Strict rule validation  
✅ **Fraud Prevention**: Multi-layer security checks  
✅ **Scalable**: Ready for production deployment  

---

## 📞 Next Steps

1. **Test the System**: Run through test scenarios
2. **Explore Dashboard**: View decision logs and metrics
3. **Customize Rules**: Edit refund_policy.txt as needed
4. **Deploy**: Follow DEPLOYMENT.md for production setup
5. **Integrate LLM**: Add Claude/GPT for natural language (optional)

---

## 📚 Documentation

- **README.md** - Full overview and features
- **ARCHITECTURE.md** - System design details
- **DEPLOYMENT.md** - Production deployment guide
- **TEST_SCENARIOS.md** - Comprehensive test cases

---

## 💡 Quick Tips

- **Default API URL**: `http://localhost:8000`
- **Streamlit Port**: `8501`
- **FastAPI Port**: `8000`
- **Sample Customer IDs**: CUST001, CUST003, CUST015
- **Sample Order IDs**: ORD-2024-001, ORD-2024-020, ORD-2024-070

---

**Version**: 1.0.0  
**Status**: Ready to Use ✅  
**Last Updated**: May 2026
