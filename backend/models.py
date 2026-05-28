from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RefundRequest(BaseModel):
    customer_id: str
    order_id: str
    reason: str
    requested_amount: Optional[float] = None
    mode: Optional[str] = None  # "rule-based" or "llm", defaults to current mode

class RefundResponse(BaseModel):
    decision: str  # "approved", "denied", "escalated"
    amount: float
    reason: str
    policy_violations: List[str]
    reasoning_log: List[str]
    requires_human_review: bool
    next_steps: str

class CustomerInfo(BaseModel):
    customer_id: str
    name: str
    email: str
    account_status: str
    total_spent: float

class OrderInfo(BaseModel):
    order_id: str
    customer_id: str
    order_date: str
    purchase_amount: float
    items: List[str]
    product_category: str
    is_final_sale: bool
    days_since_purchase: int
    status: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ConversationHistory(BaseModel):
    messages: List[ChatMessage]
    refund_decisions: List[RefundResponse] = []
