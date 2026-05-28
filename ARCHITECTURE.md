# System Architecture

## 🏗️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                             │
│                                                                    │
│  Streamlit Web UI                                                 │
│  ├─ Customer Support Interface (Customer View)                   │
│  │  ├─ Refund Request Form (Input: customer_id, order_id, etc)  │
│  │  ├─ Real-time Result Display                                  │
│  │  └─ Decision Reasoning Log Viewer                             │
│  │                                                                │
│  └─ Admin Dashboard (Management View)                            │
│     ├─ Summary Metrics & KPIs                                    │
│     ├─ Recent Requests Table                                     │
│     └─ Detailed Decision Logs with Full Reasoning                │
└──────────────────────────────────────────────────────────────────┘
                            ↓ HTTPS/HTTP
┌──────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                            │
│                                                                    │
│  FastAPI Application Server (main.py)                            │
│  ├─ /api/refund/process (POST) → RefundResponse                 │
│  ├─ /api/admin/dashboard (GET) → Dashboard Data                 │
│  ├─ /api/admin/conversation-log (GET) → History                 │
│  ├─ /api/chat (POST) → Chat Response                            │
│  ├─ /api/policy (GET) → Refund Policy                           │
│  └─ /health (GET) → Service Status                               │
│                                                                    │
│  CORS Middleware (Allow all origins for dev)                     │
│  Error Handling & Logging Middleware                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                           │
│                                                                    │
│  Refund Agent (agent.py)                                         │
│  ├─ check_eligibility_rules()                                    │
│  │  ├─ Verify order belongs to customer                          │
│  │  ├─ Check customer account status                             │
│  │  ├─ Verify order delivery status                              │
│  │  ├─ Check final sale flag                                     │
│  │  ├─ Validate 30-day window                                    │
│  │  └─ Check amount threshold ($500)                             │
│  │                                                                │
│  └─ process_refund_request()                                     │
│     ├─ Run eligibility checks                                    │
│     ├─ Determine decision (approved/denied/escalated)            │
│     ├─ Generate reasoning log                                    │
│     └─ Return structured response                                │
│                                                                    │
│  Reasoning Logger                                                │
│  ├─ Log all decision steps                                       │
│  ├─ Track tool calls                                             │
│  ├─ Record policy rules checked                                  │
│  └─ Generate audit trail                                         │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                              │
│                                                                    │
│  Tools Module (tools.py)                                         │
│  ├─ get_customer_info(customer_id)                               │
│  ├─ get_order_info(order_id)                                     │
│  ├─ verify_order_customer(customer_id, order_id)                 │
│  └─ get_refund_policy()                                          │
│                                                                    │
│  Database Class                                                  │
│  ├─ In-memory JSON loader                                        │
│  ├─ Customer lookup (O(1))                                       │
│  ├─ Order lookup (O(1))                                          │
│  └─ Policy retrieval                                             │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│                      DATA STORAGE LAYER                           │
│                                                                    │
│  JSON Files (Synthetic Data)                                     │
│  ├─ customers.json (15 profiles with status/history)             │
│  ├─ orders.json (27 orders with all details)                     │
│  └─ refund_policy.txt (Corporate policy rules)                   │
│                                                                    │
│  Memory Storage                                                  │
│  └─ Conversation history (runtime)                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Sequence Diagram

```
Customer/Admin              Streamlit              FastAPI              Agent                 Tools/DB
    │                           │                      │                  │                      │
    │─ Enter refund details ─→  │                      │                  │                      │
    │                           │                      │                  │                      │
    │                           │─ POST /refund/process ──→              │                      │
    │                           │                      │                  │                      │
    │                           │                      │─ process_refund_request() ──→          │
    │                           │                      │                  │                      │
    │                           │                      │                  │─ verify_order_customer ──→ │
    │                           │                      │                  │                      │  
    │                           │                      │                  │← order found ────── │
    │                           │                      │                  │                      │
    │                           │                      │                  │─ get_customer_info ──→ │
    │                           │                      │                  │                      │
    │                           │                      │                  │← customer data ───── │
    │                           │                      │                  │                      │
    │                           │                      │                  │─ get_order_info ──→  │
    │                           │                      │                  │                      │
    │                           │                      │                  │← order data ────── │
    │                           │                      │                  │                      │
    │                           │                      │                  │─ check_eligibility ──→ │
    │                           │                      │                  │                      │
    │                           │                      │                  │  [Apply policy rules] │
    │                           │                      │                  │  [Log all steps]      │
    │                           │                      │                  │                      │
    │                           │                      │                  │← decision ─────────── │
    │                           │                      │← RefundResponse ─│                      │
    │                           │                      │                  │                      │
    │                           │← JSON response ─────│                  │                      │
    │                           │                      │                  │                      │
    │← Display result ──────────│                      │                  │                      │
    │ - Decision badge                                │                  │                      │
    │ - Amount & reason                               │                  │                      │
    │ - Reasoning log                                 │                  │                      │
```

---

## 📊 Data Model & Schema

### Customer Data Structure
```json
{
  "customer_id": "string",           // Unique identifier
  "name": "string",                  // Full name
  "email": "string",                 // Contact email
  "phone": "string",                 // Phone number
  "account_status": "enum",          // "active" | "suspended" | "vip"
  "total_spent": "float",            // Lifetime purchase amount
  "orders": ["array of order_ids"]   // Order history
}
```

### Order Data Structure
```json
{
  "order_id": "string",              // Unique order ID
  "customer_id": "string",           // Foreign key to customer
  "order_date": "date-string",       // ISO 8601 format
  "purchase_amount": "float",        // Order total in USD
  "items": ["array of strings"],     // Product names
  "product_category": "string",      // Electronics, Jewelry, etc
  "is_final_sale": "boolean",        // Non-refundable flag
  "days_since_purchase": "integer",  // Calculated from order_date
  "status": "string"                 // "delivered", "pending", etc
}
```

### Refund Decision Structure
```json
{
  "decision": "string",              // "approved" | "denied" | "escalated"
  "amount": "float",                 // Refund amount in USD
  "reason": "string",                // Human-readable reason
  "policy_violations": ["array"],    // List of violated rules
  "reasoning_log": ["array"],        // Step-by-step decision trace
  "requires_human_review": "boolean",// Escalation flag
  "next_steps": "string"             // Action for customer
}
```

---

## 🔀 Decision Logic Flow

```
┌─ START ─┐
    │
    ├─→ [VERIFY ORDER EXISTS & BELONGS TO CUSTOMER]
    │   ├─ Success → Continue
    │   └─ Fail → AUTO-DENY
    │
    ├─→ [CHECK CUSTOMER STATUS]
    │   ├─ suspended → AUTO-DENY
    │   ├─ active/vip → Continue
    │   └─ Fail → AUTO-DENY
    │
    ├─→ [CHECK ORDER DELIVERED]
    │   ├─ Yes → Continue
    │   └─ No → AUTO-DENY
    │
    ├─→ [CHECK FINAL SALE FLAG]
    │   ├─ Yes → AUTO-DENY (NEVER REFUND)
    │   └─ No → Continue
    │
    ├─→ [CHECK 30-DAY WINDOW]
    │   ├─ ≤30 days → Continue
    │   └─ >30 days → AUTO-DENY
    │
    ├─→ [CHECK REFUND AMOUNT]
    │   ├─ ≤$500 → AUTO-APPROVE
    │   ├─ >$500 (non-VIP) → ESCALATE
    │   ├─ $500-$750 (VIP) → Consider auto-approve
    │   └─ >$750 (VIP) → ESCALATE
    │
    └─→ [RETURN DECISION]
        ├─ APPROVED ✅
        ├─ DENIED ❌
        └─ ESCALATED ⚠️
```

---

## 🛡️ Security & Validation Layers

### Input Validation
```
Request → FastAPI Model Validation → Type Checking → Error Handling
```

- Pydantic models validate all inputs
- Type hints ensure data consistency
- Custom validators check business logic
- HTTP exception handlers return proper errors

### Policy Enforcement Layer
```
Request → Verify Order Belongs to Customer 
       → Check Account Status 
       → Apply Policy Rules 
       → Log All Decisions
```

### Anti-Fraud Measures
1. **Order Verification**: Confirm order belongs to requesting customer
2. **Account Status Checking**: Suspended accounts cannot get refunds
3. **Policy Immutability**: Rules cannot be bypassed by prompt injection
4. **Audit Trail**: All decisions logged with full reasoning
5. **Rate Limiting**: Future: Detect abuse patterns

---

## 🎯 Agent Decision Algorithm

### Pseudo-code
```
function processRefundRequest(customer_id, order_id, reason, amount):
    log("Starting eligibility check")
    
    # Step 1: Verify relationship
    if not verifyOrderCustomer(customer_id, order_id):
        return DENY("Order does not belong to customer")
    
    # Step 2: Get customer data
    customer = getCustomerInfo(customer_id)
    if not customer.found:
        return DENY("Customer not found")
    
    # Step 3: Check account status
    if customer.status == "suspended":
        return DENY("Account suspended")
    
    # Step 4: Get order data
    order = getOrderInfo(order_id)
    if not order.found:
        return DENY("Order not found")
    
    # Step 5: Check delivery
    if order.status != "delivered":
        return DENY("Order not delivered")
    
    # Step 6: Check final sale
    if order.is_final_sale:
        return DENY("Final sale - non-refundable")
    
    # Step 7: Check time window
    if order.days_since_purchase > 30:
        return DENY("Outside 30-day refund window")
    
    # Step 8: Determine decision
    refund_amount = amount or order.purchase_amount
    
    if refund_amount > 500:
        if customer.status == "vip" and refund_amount <= 750:
            return APPROVE(refund_amount)
        else:
            return ESCALATE(refund_amount)
    
    return APPROVE(refund_amount)
```

---

## 📈 Performance Characteristics

### Time Complexity
- Customer lookup: **O(1)** - Direct dictionary access
- Order lookup: **O(1)** - Direct dictionary access
- Eligibility check: **O(1)** - Fixed number of checks
- Overall decision: **O(1)** - Constant time regardless of scale

### Space Complexity
- Customer storage: **O(n)** where n = number of customers
- Order storage: **O(m)** where m = number of orders
- Conversation history: **O(r)** where r = number of requests

### Expected Response Times
- Simple approval: ~50-100ms
- Complex denial: ~75-150ms
- Escalation: ~75-150ms
- Dashboard load: ~200-500ms (depends on history size)

---

## 🔌 API Contract Specifications

### Request/Response Examples

#### /api/refund/process

**Request:**
```json
{
  "customer_id": "CUST001",
  "order_id": "ORD-2024-001",
  "reason": "Product arrived damaged",
  "requested_amount": 400.50
}
```

**Response (200 OK):**
```json
{
  "decision": "approved",
  "amount": 400.50,
  "reason": "Refund approved for Laptop Stand",
  "policy_violations": [],
  "reasoning_log": [
    "[14:23:45] Starting eligibility check...",
    "[14:23:45] Tool Call: verify_order_customer",
    "[14:23:45] ✓ Order verified to belong to customer",
    "..."
  ],
  "requires_human_review": false,
  "next_steps": "Refund will be processed to your original payment method within 3-5 business days"
}
```

---

## 🚀 Technology Stack

### Backend
- **Framework**: FastAPI (Python async web framework)
- **Server**: Uvicorn (ASGI server)
- **Validation**: Pydantic (data validation)
- **Data**: JSON files (scalable to PostgreSQL)

### Frontend
- **Framework**: Streamlit (rapid UI development)
- **HTTP Client**: Requests library
- **Data Display**: Pandas DataFrames
- **State Management**: Streamlit Session State

### DevOps
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Version Control**: Git/GitHub

### Optional Integrations (Future)
- **LLMs**: OpenAI API, Anthropic Claude
- **Databases**: PostgreSQL, MongoDB
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack, CloudWatch
- **CI/CD**: GitHub Actions, GitLab CI
- **Cloud**: AWS, GCP, Azure

---

## 📝 Configuration & Extensibility

### Adding New Policy Rules

1. **Update refund_policy.txt** with new rules
2. **Extend check_eligibility_rules()** in agent.py
3. **Add validation logic** to decision tree
4. **Log new checks** in reasoning log
5. **Test with TEST_SCENARIOS.md**

### Adding New Tools

1. **Define tool function** in tools.py
2. **Add to TOOLS array** with metadata
3. **Call via execute_tool()** in agent logic
4. **Log tool invocations** in reasoning

### Integrating LLM (Future Enhancement)

```python
from langchain.llms import ChatOpenAI
from langchain.tools import tool

llm = ChatOpenAI(model="gpt-4", api_key=api_key)

@tool("verify_customer")
def verify_customer_tool(customer_id: str) -> str:
    """Verify customer eligibility"""
    # Tool implementation
    pass

# Use with LangGraph for agentic loop
```

---

**Architecture Version**: 1.0
**Last Updated**: March 2024
