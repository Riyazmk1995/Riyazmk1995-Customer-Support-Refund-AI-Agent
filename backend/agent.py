import json
import re
from typing import Dict, List, Optional
from tools import execute_tool, get_refund_policy
from datetime import datetime

class RefundAgent:
    """AI Agent for processing refund requests"""
    
    def __init__(self, api_key: str = None):
        """Initialize the agent with LLM API key"""
        self.api_key = api_key
        self.reasoning_log: List[str] = []
        self.use_llm = api_key is not None
    
    def log_reasoning(self, step: str):
        """Add step to reasoning log"""
        self.reasoning_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {step}")
    
    def check_eligibility_rules(self, customer_id: str, order_id: str, requested_amount: float) -> Dict:
        """Check refund eligibility against policy rules"""
        violations = []
        checks_passed = []
        
        self.log_reasoning(f"Starting eligibility check for customer {customer_id}, order {order_id}")
        
        # Step 1: Verify order belongs to customer
        self.log_reasoning("Tool Call: verify_order_customer")
        verify_result = json.loads(execute_tool("verify_order_customer", customer_id=customer_id, order_id=order_id))
        
        if not verify_result.get("verified"):
            violations.append("Order does not belong to this customer")
            self.log_reasoning("❌ VIOLATION: Order does not belong to customer")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        self.log_reasoning("✓ Order verified to belong to customer")
        checks_passed.append("Order belongs to customer")
        
        # Step 2: Get customer info
        self.log_reasoning("Tool Call: get_customer_info")
        customer_result = json.loads(execute_tool("get_customer_info", customer_id=customer_id))
        
        if not customer_result.get("found"):
            violations.append("Customer not found in system")
            self.log_reasoning("❌ VIOLATION: Customer not found")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        customer_status = customer_result.get("account_status")
        self.log_reasoning(f"Customer status: {customer_status}")
        
        if customer_status == "suspended":
            violations.append("Customer account is suspended - no refunds allowed")
            self.log_reasoning("❌ VIOLATION: Customer account suspended")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        checks_passed.append(f"Customer account is active ({customer_status})")
        self.log_reasoning("✓ Customer account status valid")
        
        # Step 3: Get order info
        self.log_reasoning("Tool Call: get_order_info")
        order_result = json.loads(execute_tool("get_order_info", order_id=order_id))
        
        if not order_result.get("found"):
            violations.append("Order not found in system")
            self.log_reasoning("❌ VIOLATION: Order not found")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        # Step 4: Check if order is delivered
        order_status = order_result.get("status")
        self.log_reasoning(f"Order status: {order_status}")
        
        if order_status != "delivered":
            violations.append(f"Order not delivered (status: {order_status})")
            self.log_reasoning("❌ VIOLATION: Order not delivered")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        checks_passed.append("Order has been delivered")
        self.log_reasoning("✓ Order delivered")
        
        # Step 5: Check final sale status
        is_final_sale = order_result.get("is_final_sale", False)
        self.log_reasoning(f"Final sale status: {is_final_sale}")
        
        if is_final_sale:
            violations.append("This is a final sale item - non-refundable per policy")
            self.log_reasoning("❌ VIOLATION: Final sale item - cannot be refunded under any circumstances")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        checks_passed.append("Item is not marked as final sale")
        self.log_reasoning("✓ Item is not final sale")
        
        # Step 6: Check purchase window (30 days)
        days_since = order_result.get("days_since_purchase", 0)
        self.log_reasoning(f"Days since purchase: {days_since}")
        
        if days_since > 30:
            violations.append(f"Purchase was {days_since} days ago (policy allows max 30 days)")
            self.log_reasoning("❌ VIOLATION: Purchase outside 30-day refund window")
            return {"eligible": False, "violations": violations, "checks_passed": checks_passed}
        
        checks_passed.append(f"Within 30-day refund window ({days_since} days ago)")
        self.log_reasoning("✓ Within refund window")
        
        # Step 7: Check amount threshold (>$500 needs escalation)
        refund_amount = requested_amount or order_result.get("purchase_amount", 0)
        self.log_reasoning(f"Refund amount requested: ${refund_amount}")
        
        escalation_needed = False
        if refund_amount > 500:
            self.log_reasoning("⚠ Amount exceeds $500 threshold - requires human escalation")
            escalation_needed = True
        
        # All checks passed for auto-approval eligibility
        self.log_reasoning("✓ All eligibility checks passed")
        
        return {
            "eligible": True,
            "violations": violations,
            "checks_passed": checks_passed,
            "escalation_needed": escalation_needed,
            "customer_status": customer_status,
            "order_amount": order_result.get("purchase_amount"),
            "days_since_purchase": days_since,
            "product_category": order_result.get("product_category"),
            "items": order_result.get("items")
        }
    
    def process_refund_request(self, customer_id: str, order_id: str, reason: str, requested_amount: Optional[float] = None) -> Dict:
        """Process a refund request and make a decision"""
        self.reasoning_log = []  # Reset log for new request
        self.log_reasoning(f"=== NEW REFUND REQUEST ===")
        self.log_reasoning(f"Customer: {customer_id}")
        self.log_reasoning(f"Order: {order_id}")
        self.log_reasoning(f"Reason: {reason}")
        self.log_reasoning(f"Requested Amount: ${requested_amount}" if requested_amount else "Full refund")
        
        # Run eligibility checks
        eligibility = self.check_eligibility_rules(customer_id, order_id, requested_amount)
        
        if not eligibility["eligible"]:
            # Determine if auto-deny or needs escalation
            violations = eligibility["violations"]
            
            # Check for policy violations that warrant immediate denial
            auto_deny_reasons = [
                "Customer account is suspended",
                "final sale",
                "Order does not belong to this customer",
                "Purchase was"  # Outside refund window
            ]
            
            should_deny = any(any(reason in str(v) for reason in auto_deny_reasons) for v in violations)
            
            if should_deny:
                self.log_reasoning("❌ AUTO-DENY: Policy violation detected")
                return {
                    "decision": "denied",
                    "amount": 0,
                    "reason": " ".join(violations),
                    "policy_violations": violations,
                    "reasoning_log": self.reasoning_log,
                    "requires_human_review": False,
                    "next_steps": "This refund request violates our refund policy. Please review the policy terms or contact customer support for exceptions."
                }
            else:
                self.log_reasoning("⚠ ESCALATION NEEDED: Additional review required")
                return {
                    "decision": "escalated",
                    "amount": requested_amount or 0,
                    "reason": "Refund request requires human review due to: " + "; ".join(violations),
                    "policy_violations": violations,
                    "reasoning_log": self.reasoning_log,
                    "requires_human_review": True,
                    "next_steps": "Your request has been escalated to our management team for review. You will receive an update within 24-48 hours."
                }
        
        # Eligibility checks passed - now determine decision
        self.log_reasoning("Processing decision logic...")
        
        refund_amount = requested_amount or eligibility.get("order_amount", 0)
        escalation_needed = eligibility.get("escalation_needed", False)
        customer_status = eligibility.get("customer_status")
        
        # Check for VIP enhancement
        if customer_status == "vip" and refund_amount > 500 and refund_amount <= 750:
            self.log_reasoning("ℹ VIP customer with amount $500-$750: Management review recommended")
            escalation_needed = False  # Can be auto-approved for VIP
        
        if escalation_needed and customer_status != "vip":
            self.log_reasoning("❌ DECISION: ESCALATION - Amount exceeds $500 threshold")
            return {
                "decision": "escalated",
                "amount": refund_amount,
                "reason": f"Refund amount of ${refund_amount} exceeds the ${500} auto-approval threshold and requires human review",
                "policy_violations": [],
                "reasoning_log": self.reasoning_log,
                "requires_human_review": True,
                "next_steps": f"Your ${refund_amount} refund request has been escalated to management. Expected response within 2-3 business days."
            }
        
        # Auto-approve
        self.log_reasoning("✓ DECISION: AUTO-APPROVED")
        self.log_reasoning(f"Refund amount: ${refund_amount}")
        self.log_reasoning(f"Processed at: {datetime.now()}")
        
        return {
            "decision": "approved",
            "amount": refund_amount,
            "reason": f"Refund approved for {eligibility.get('items', ['items'])[0]} (Order: {order_id})",
            "policy_violations": [],
            "reasoning_log": self.reasoning_log,
            "requires_human_review": False,
            "next_steps": f"Your ${refund_amount} refund has been approved. You should see the credit back to your original payment method within 3-5 business days."
        }

def create_agent(api_key: Optional[str] = None) -> RefundAgent:
    """Factory function to create an agent instance"""
    return RefundAgent(api_key=api_key)
