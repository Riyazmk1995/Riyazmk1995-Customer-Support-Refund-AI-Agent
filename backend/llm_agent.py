import os
import json
from typing import Optional, Dict, List
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tools import execute_tool, get_refund_policy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMRefundAgent:
    """AI Agent using OpenAI LLM for intelligent refund processing"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """Initialize the LLM agent with OpenAI API"""
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        # Get model from parameter, environment, or use default
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.reasoning_log: List[str] = []
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.model,
            temperature=0,  # Deterministic responses
            max_tokens=2000
        )
    
    def log_reasoning(self, step: str):
        """Add step to reasoning log"""
        self.reasoning_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {step}")
    
    def _build_context(self, customer_id: str, order_id: str) -> Dict:
        """Build customer and order context from database"""
        self.log_reasoning("Building context from database...")
        
        # Get customer info
        self.log_reasoning("Tool Call: get_customer_info")
        customer_result = json.loads(execute_tool("get_customer_info", customer_id=customer_id))
        
        # Get order info
        self.log_reasoning("Tool Call: get_order_info")
        order_result = json.loads(execute_tool("get_order_info", order_id=order_id))
        
        # Verify relationship
        self.log_reasoning("Tool Call: verify_order_customer")
        verify_result = json.loads(execute_tool("verify_order_customer", customer_id=customer_id, order_id=order_id))
        
        return {
            "customer": customer_result,
            "order": order_result,
            "verified": verify_result.get("verified", False)
        }
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM"""
        policy = get_refund_policy()
        
        return f"""You are an expert AI Customer Support Agent specialized in processing e-commerce refund requests.

Your responsibilities:
1. Analyze refund requests based on the provided corporate refund policy
2. Make decisions: APPROVED, DENIED, or ESCALATED
3. Provide clear reasoning for every decision
4. Identify policy violations
5. Protect company interests while being fair to customers

CRITICAL RULES (Non-negotiable):
- Final sale items are NEVER refundable under ANY circumstances
- Refunds over $500 MUST be escalated to human management
- Suspended customer accounts cannot get refunds
- Refunds must be requested within exactly 30 days of purchase
- Verify customer information matches the order

REFUND POLICY:
{policy}

Your response MUST be a valid JSON object with this structure:
{{
    "decision": "approved|denied|escalated",
    "amount": <number>,
    "reason": "<explanation>",
    "policy_violations": [<list of violations>],
    "requires_human_review": <boolean>,
    "next_steps": "<customer action>"
}}

Be strict with policy enforcement. Never bend the rules based on customer emotion or aggressive language."""
    
    def process_refund_request(
        self, 
        customer_id: str, 
        order_id: str, 
        reason: str,
        requested_amount: Optional[float] = None
    ) -> Dict:
        """Process a refund request using LLM with policy validation"""
        
        self.reasoning_log = []  # Reset log
        self.log_reasoning("=== NEW REFUND REQUEST (LLM Mode) ===")
        self.log_reasoning(f"Customer: {customer_id}")
        self.log_reasoning(f"Order: {order_id}")
        self.log_reasoning(f"Reason: {reason}")
        
        try:
            # Build context
            context = self._build_context(customer_id, order_id)
            self.log_reasoning(f"Context built. Order verified: {context['verified']}")
            
            if not context['verified']:
                self.log_reasoning("❌ Order-Customer verification failed")
                return {
                    "decision": "denied",
                    "amount": 0,
                    "reason": "Order does not belong to this customer",
                    "policy_violations": ["Order verification failed"],
                    "reasoning_log": self.reasoning_log,
                    "requires_human_review": False,
                    "next_steps": "Please verify your customer ID and order ID"
                }
            
            # Build context string for LLM
            context_str = f"""
CUSTOMER INFORMATION:
{json.dumps(context['customer'], indent=2)}

ORDER INFORMATION:
{json.dumps(context['order'], indent=2)}

REFUND REQUEST:
- Reason: {reason}
- Requested Amount: ${requested_amount if requested_amount else 'Full refund (${:.2f})'.format(context['order'].get('purchase_amount', 0))}

Please analyze this refund request against the policy and provide your decision in the specified JSON format.
"""
            
            self.log_reasoning("Calling OpenAI LLM for decision analysis...")
            self.log_reasoning(f"Model: {self.model}")
            
            # Call LLM with policy context
            system_prompt = self._create_system_prompt()
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_str)
            ]
            
            response = self.llm(messages)
            self.log_reasoning("✓ LLM responded")
            
            # Parse LLM response
            response_text = response.content
            self.log_reasoning(f"LLM Response: {response_text[:100]}...")
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response_text)
                
                self.log_reasoning(f"Decision: {result.get('decision', 'unknown').upper()}")
                self.log_reasoning(f"Amount: ${result.get('amount', 0):.2f}")
                
                # Add reasoning log to result
                result["reasoning_log"] = self.reasoning_log
                
                return result
                
            except json.JSONDecodeError as e:
                self.log_reasoning(f"❌ Failed to parse LLM response as JSON: {str(e)}")
                
                # Fallback to rule-based decision
                self.log_reasoning("⚠️ Falling back to rule-based decision")
                return self._fallback_decision(context, reason, requested_amount)
        
        except Exception as e:
            self.log_reasoning(f"❌ Error: {str(e)}")
            
            # Fallback on any error
            return {
                "decision": "escalated",
                "amount": requested_amount or 0,
                "reason": f"System error during processing: {str(e)}. Request escalated for manual review.",
                "policy_violations": [],
                "reasoning_log": self.reasoning_log,
                "requires_human_review": True,
                "next_steps": "Your request has been escalated to our support team due to a processing error. We'll contact you within 24 hours."
            }
    
    def _fallback_decision(self, context: Dict, reason: str, requested_amount: Optional[float]) -> Dict:
        """Fallback to rule-based decision if LLM fails"""
        violations = []
        
        # Check basic rules
        if not context['order'].get('found'):
            violations.append("Order not found")
        
        if context['customer'].get('account_status') == 'suspended':
            violations.append("Customer account is suspended")
        
        if context['order'].get('is_final_sale'):
            violations.append("Item is final sale - non-refundable")
        
        if context['order'].get('days_since_purchase', 0) > 30:
            violations.append("Purchase outside 30-day refund window")
        
        if violations:
            return {
                "decision": "denied",
                "amount": 0,
                "reason": "; ".join(violations),
                "policy_violations": violations,
                "reasoning_log": self.reasoning_log,
                "requires_human_review": False,
                "next_steps": "Your refund request cannot be processed due to policy violations."
            }
        
        # Check amount threshold
        refund_amount = requested_amount or context['order'].get('purchase_amount', 0)
        
        if refund_amount > 500:
            return {
                "decision": "escalated",
                "amount": refund_amount,
                "reason": f"Refund amount ${refund_amount} exceeds auto-approval threshold",
                "policy_violations": [],
                "reasoning_log": self.reasoning_log,
                "requires_human_review": True,
                "next_steps": "Your request has been escalated for human review"
            }
        
        return {
            "decision": "approved",
            "amount": refund_amount,
            "reason": f"Refund approved via fallback logic",
            "policy_violations": [],
            "reasoning_log": self.reasoning_log,
            "requires_human_review": False,
            "next_steps": f"Your ${refund_amount} refund has been approved"
        }

def create_llm_agent(api_key: Optional[str] = None, model: str = None) -> LLMRefundAgent:
    """Factory function to create an LLM agent instance"""
    # Use provided model, environment variable, or default
    model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    return LLMRefundAgent(api_key=api_key, model=model)
