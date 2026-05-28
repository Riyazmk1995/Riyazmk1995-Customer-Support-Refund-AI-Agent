# 🤖 LLM Integration Guide

Enable OpenAI GPT-3.5-turbo for intelligent refund decisions with policy validation.

---

## 🚀 Quick Setup (LLM Mode)

### Step 1: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to "API Keys" → "Create new secret key"
4. Copy your API key (keep it secret!)

### Step 2: Configure Environment

#### Option A: Using .env File (Recommended)

```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add your OpenAI API key
USE_LLM=true
OPENAI_API_KEY=sk-your-actual-key-here
```

#### Option B: Set Environment Variables Directly

**Windows (PowerShell):**
```powershell
$env:USE_LLM="true"
$env:OPENAI_API_KEY="sk-your-actual-key-here"
```

**Linux/Mac (Bash):**
```bash
export USE_LLM=true
export OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Update Backend Dependencies

```bash
cd backend

# If using venv:
venv\Scripts\activate

# Install updated requirements
pip install -r requirements.txt
```

### Step 4: Start the Backend

```bash
python -m uvicorn main:app --reload
```

You should see:
```
🤖 Initializing LLM-based Refund Agent (OpenAI)
```

---

## 🧪 Test LLM Mode

### Check Agent Type

```bash
curl http://localhost:8000/api/agent-info

# Response:
# {
#   "agent_type": "LLM (GPT-3.5-turbo)",
#   "use_llm": true,
#   "has_openai_key": true,
#   "version": "1.0.1"
# }
```

### Test Refund Processing

```bash
curl -X POST http://localhost:8000/api/refund/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "order_id": "ORD-2024-001",
    "reason": "The product stopped working after 2 weeks",
    "requested_amount": 300
  }'
```

**Response:**
```json
{
  "decision": "approved",
  "amount": 300,
  "reason": "Item quality issue within acceptable refund period",
  "policy_violations": [],
  "reasoning_log": [
    "[14:23:45] === NEW REFUND REQUEST (LLM Mode) ===",
    "[14:23:45] Customer: CUST001",
    "[14:23:45] Order: ORD-2024-001",
    "[14:23:45] Building context from database...",
    "[14:23:45] Tool Call: get_customer_info",
    "[14:23:45] Calling OpenAI LLM for decision analysis...",
    "[14:23:45] Model: gpt-3.5-turbo",
    "[14:23:45] ✓ LLM responded",
    "[14:23:45] Decision: APPROVED"
  ],
  "requires_human_review": false,
  "next_steps": "Your refund has been approved. You should see the credit within 3-5 business days."
}
```

---

## 🎯 How LLM Mode Works

```
Customer Request
      ↓
API Receives Request
      ↓
Database Context Loaded
  ├─ Customer Info
  ├─ Order Details
  └─ Relationship Verified
      ↓
LLM Analysis (GPT-3.5)
  ├─ Reads Refund Policy
  ├─ Analyzes Customer Reason
  ├─ Evaluates All Factors
  └─ Makes Decision
      ↓
Policy Validation Layer
  ├─ Checks Final Sale Flag
  ├─ Verifies Amount Threshold
  ├─ Validates Account Status
  └─ Enforces Hard Rules
      ↓
Response with Reasoning
  ├─ Decision (approved/denied/escalated)
  ├─ Amount
  ├─ Reasoning Log
  └─ Next Steps
```

---

## 💡 Key Advantages of LLM Mode

✅ **Intelligent Reasoning** - Understands nuances in customer requests  
✅ **Natural Language** - Processes customer explanations  
✅ **Context Awareness** - Considers customer history and patterns  
✅ **Better Explanations** - Provides human-readable decision reasons  
✅ **Policy Enforcement** - Still validates against strict rules  
✅ **Audit Trail** - Complete LLM call logs  
✅ **Fallback Logic** - Reverts to rule-based if LLM fails  

---

## 🔒 Policy Enforcement with LLM

**Hard Rules (Always Enforced):**
- ❌ Final sale items are NEVER refundable
- ❌ Amounts >$500 are ALWAYS escalated
- ❌ Suspended accounts are ALWAYS denied
- ❌ >30 days is ALWAYS denied

**LLM-Analyzed Factors:**
- ✓ Reason quality assessment
- ✓ Customer tone analysis
- ✓ Damage/defect evaluation
- ✓ Pattern recognition
- ✓ Nuanced decision-making

---

## 📊 Example Scenarios

### Scenario 1: Quality Issue (LLM Decides)
```
Request:
- Customer: CUST001
- Order: ORD-2024-001 ($300 item)
- Reason: "Product broke after 2 weeks, poor quality"

LLM Analysis:
- Recognizes legitimate quality concern
- Within refund period (25 days)
- Amount under threshold
- Decision: APPROVED ✅

Agent Reasoning:
[14:23:45] LLM: "Customer reports legitimate quality issue..."
[14:23:46] LLM: "Item within acceptable refund period..."
[14:23:47] LLM: "Amount qualifies for auto-approval..."
[14:23:48] Decision: APPROVED
```

### Scenario 2: Final Sale (Policy Enforced)
```
Request:
- Customer: CUST001
- Order: ORD-2024-002 (Final Sale = true, $500)
- Reason: "Changed my mind"

Agent Logic:
1. ❌ Checks final_sale flag
2. Policy violation detected
3. Decision: DENIED ❌

Agent Reasoning:
[14:24:00] ❌ Order verification failed
[14:24:01] ❌ VIOLATION: Final sale item - non-refundable
[14:24:02] Decision: DENIED
```

### Scenario 3: Large Amount (Escalation)
```
Request:
- Customer: CUST003
- Order: ORD-2024-021 ($1,500)
- Reason: "Item doesn't work as advertised"

Agent Logic:
1. ✓ LLM analysis: Legitimate complaint
2. ❌ Amount >$500 threshold
3. Decision: ESCALATED ⚠️

Agent Reasoning:
[14:25:00] LLM: "Customer has valid complaint..."
[14:25:01] LLM: "Issue warrants investigation..."
[14:25:02] ❌ Amount $1,500 exceeds $500 threshold
[14:25:03] Decision: ESCALATED (requires human review)
```

---

## 🛠️ Troubleshooting

### Error: "OpenAI API key not provided"

**Fix:** Make sure your .env file has:
```bash
USE_LLM=true
OPENAI_API_KEY=sk-your-actual-key-here
```

Then restart the backend:
```bash
# Kill the current process (Ctrl+C)
# Restart:
python -m uvicorn main:app --reload
```

### Error: "Failed to parse LLM response as JSON"

**Cause:** LLM returned unexpected format  
**Fix:** System automatically falls back to rule-based decision  
**Check logs:** Look at terminal output for error details

### High API Costs

**Monitor Usage:**
- Each request calls OpenAI once
- ~0.01-0.05 cent per request (GPT-3.5-turbo)
- 1000 requests ≈ $0.50-2.50

**Optimize:**
- Use `gpt-3.5-turbo` (cheapest, faster)
- Implement request caching
- Batch similar requests

### Response Too Slow

**Optimization:**
- LLM calls take 1-3 seconds
- Use `gpt-3.5-turbo` (faster than GPT-4)
- Check internet connection
- Verify OpenAI API status

---

## 📈 Cost Estimation

### GPT-3.5-turbo Pricing

| Usage | Cost |
|-------|------|
| 100 requests/day | ~$1.50-7.50/month |
| 1,000 requests/day | ~$15-75/month |
| 10,000 requests/day | ~$150-750/month |

**Formula:**
- Input: ~0.0005¢ per token
- Output: ~0.0015¢ per token
- Average request: 500 tokens = ~$0.001

---

## 🔄 Switching Modes

### Use LLM Mode
```bash
# In .env or environment:
USE_LLM=true
OPENAI_API_KEY=sk-your-key-here

# Restart backend
python -m uvicorn main:app --reload

# Check agent type:
curl http://localhost:8000/api/agent-info
# Shows: "agent_type": "LLM (GPT-3.5-turbo)"
```

### Use Rule-Based Mode
```bash
# In .env or environment:
USE_LLM=false

# Or just unset:
# OPENAI_API_KEY=

# Restart backend
python -m uvicorn main:app --reload

# Check agent type:
curl http://localhost:8000/api/agent-info
# Shows: "agent_type": "Rule-based"
```

---

## 🎓 Advanced: Custom System Prompt

Edit `backend/llm_agent.py` in the `_create_system_prompt()` method to customize:

```python
def _create_system_prompt(self) -> str:
    """Create system prompt for the LLM"""
    policy = get_refund_policy()
    
    return f"""You are an expert AI Customer Support Agent...
    
    # Add your custom instructions here
    
    COMPANY VALUES:
    - Customer satisfaction (but protect company interests)
    - Fair decision-making
    - Quick resolutions
    """
```

---

## 📞 Next Steps

1. **Get OpenAI API Key** - Sign up at platform.openai.com
2. **Update .env** - Add `USE_LLM=true` and your API key
3. **Install Dependencies** - `pip install -r requirements.txt`
4. **Test** - Use curl or Streamlit UI to process requests
5. **Monitor Costs** - Check OpenAI dashboard for usage
6. **Optimize** - Adjust prompts based on decisions

---

## 🚀 Deployment with LLM

### Docker with LLM

Update your Docker environment:
```yaml
# docker-compose.yml
environment:
  - USE_LLM=true
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

Pass secret at runtime:
```bash
OPENAI_API_KEY=sk-your-key docker-compose up -d
```

### Production Best Practices

✅ Use `.env` file (never commit it!)  
✅ Use IAM roles in cloud (not raw API keys)  
✅ Set up monitoring and alerts  
✅ Implement rate limiting  
✅ Cache repeated requests  
✅ Use async calls for scale  
✅ Monitor OpenAI usage daily  

---

**Version**: 1.0.1  
**LLM Model**: GPT-3.5-turbo  
**Status**: Production Ready ✅
