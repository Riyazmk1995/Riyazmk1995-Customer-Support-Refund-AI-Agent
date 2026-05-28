from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import json
import os
from datetime import datetime
from models import RefundRequest, RefundResponse, ChatMessage, ConversationHistory
from agent import create_agent
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Customer Support Refund Agent",
    description="An AI agent for processing e-commerce refunds with optional LLM integration",
    version="1.0.1"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Initialize rule-based agent (always available)
logger.info("📋 Initializing Rule-based Refund Agent")
rule_based_agent = create_agent()

# Initialize LLM agent if API key is available
llm_agent = None
LLM_AVAILABLE = False
if OPENAI_API_KEY:
    try:
        logger.info("🤖 Initializing LLM-based Refund Agent (OpenAI)")
        from llm_agent import create_llm_agent
        llm_agent = create_llm_agent(api_key=OPENAI_API_KEY, model=LLM_MODEL)
        LLM_AVAILABLE = True
        logger.info(f"✓ LLM Agent initialized with model: {LLM_MODEL}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize LLM agent: {str(e)}")
        LLM_AVAILABLE = False

# Determine default mode from environment
DEFAULT_MODE = os.getenv("USE_LLM", "false").lower() == "true"
# If LLM not available, always use rule-based
if not LLM_AVAILABLE:
    DEFAULT_MODE = False
    CURRENT_MODE = "rule-based"
else:
    CURRENT_MODE = "llm" if DEFAULT_MODE else "rule-based"

logger.info(f"📊 Default mode set to: {CURRENT_MODE}")

# Store conversation history for admin dashboard
conversation_history: List[dict] = []

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Refund Agent API",
        "current_mode": CURRENT_MODE,
        "llm_available": LLM_AVAILABLE,
        "llm_model": LLM_MODEL if LLM_AVAILABLE else None,
        "version": "1.0.1"
    }

@app.get("/api/agent-info")
def get_agent_info():
    """Get current agent configuration and available modes"""
    return {
        "agent_type": "LLM (GPT-3.5-turbo)" if CURRENT_MODE == "llm" else "Rule-based",
        "current_mode": CURRENT_MODE,
        "use_llm": CURRENT_MODE == "llm",
        "has_openai_key": OPENAI_API_KEY is not None,
        "llm_available": LLM_AVAILABLE,
        "llm_model": LLM_MODEL if LLM_AVAILABLE else None,
        "available_modes": ["rule-based", "llm"] if LLM_AVAILABLE else ["rule-based"],
        "version": "1.0.1"
    }

@app.post("/api/set-mode/{mode}")
def set_mode(mode: str):
    """Switch between rule-based and LLM modes"""
    global CURRENT_MODE
    
    mode = mode.lower()
    
    if mode not in ["rule-based", "llm"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode '{mode}'. Available modes: rule-based, llm"
        )
    
    if mode == "llm" and not LLM_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="LLM mode not available. OpenAI API key is not configured."
        )
    
    CURRENT_MODE = mode
    logger.info(f"🔄 Mode switched to: {mode}")
    
    return {
        "status": "success",
        "message": f"Mode switched to {mode}",
        "current_mode": CURRENT_MODE,
        "agent_type": "LLM (GPT-3.5-turbo)" if CURRENT_MODE == "llm" else "Rule-based"
    }

@app.post("/api/refund/process")
def process_refund(request: RefundRequest) -> RefundResponse:
    """
    Process a refund request
    
    Args:
        request: RefundRequest with customer_id, order_id, reason, optional requested_amount, and optional mode
        
    Returns:
        RefundResponse with decision and reasoning
    """
    try:
        # Determine which agent to use
        mode = (request.mode or CURRENT_MODE).lower() if request.mode else CURRENT_MODE
        
        if mode not in ["rule-based", "llm"]:
            logger.warning(f"Invalid mode requested: {mode}, using current mode: {CURRENT_MODE}")
            mode = CURRENT_MODE
        
        if mode == "llm" and not LLM_AVAILABLE:
            logger.warning(f"LLM mode requested but not available, falling back to rule-based")
            mode = "rule-based"
        
        # Select agent
        agent = llm_agent if mode == "llm" else rule_based_agent
        
        logger.info(f"Processing refund request for customer {request.customer_id}, order {request.order_id}")
        logger.info(f"Using mode: {mode}")
        
        # Process the refund through the agent
        result = agent.process_refund_request(
            customer_id=request.customer_id,
            order_id=request.order_id,
            reason=request.reason,
            requested_amount=request.requested_amount
        )
        
        # Create response
        response = RefundResponse(
            decision=result["decision"],
            amount=result["amount"],
            reason=result["reason"],
            policy_violations=result["policy_violations"],
            reasoning_log=result["reasoning_log"],
            requires_human_review=result["requires_human_review"],
            next_steps=result["next_steps"]
        )
        
        # Store in conversation history for admin dashboard
        conversation_history.append({
            "type": "refund_request",
            "request": request.dict(),
            "response": response.dict(),
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Refund decision: {result['decision']} using {mode} mode")
        return response
        
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing refund: {str(e)}")

@app.get("/api/admin/dashboard")
def get_admin_dashboard():
    """
    Get admin dashboard data with refund processing history and logs
    """
    try:
        # Count decisions
        approved_count = sum(1 for entry in conversation_history if entry["response"]["decision"] == "approved")
        denied_count = sum(1 for entry in conversation_history if entry["response"]["decision"] == "denied")
        escalated_count = sum(1 for entry in conversation_history if entry["response"]["decision"] == "escalated")
        
        # Calculate total amounts
        total_approved = sum(entry["response"]["amount"] for entry in conversation_history 
                           if entry["response"]["decision"] == "approved")
        total_escalated = sum(entry["response"]["amount"] for entry in conversation_history 
                            if entry["response"]["decision"] == "escalated")
        
        # Get recent requests
        recent_requests = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        
        return {
            "summary": {
                "total_requests": len(conversation_history),
                "approved": approved_count,
                "denied": denied_count,
                "escalated": escalated_count,
                "total_approved_amount": round(total_approved, 2),
                "total_escalated_amount": round(total_escalated, 2)
            },
            "recent_requests": recent_requests,
            "approval_rate": round((approved_count / len(conversation_history) * 100) if conversation_history else 0, 2)
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")

@app.get("/api/admin/conversation-log")
def get_conversation_log(limit: int = 50):
    """
    Get conversation and refund processing logs
    
    Args:
        limit: Maximum number of recent entries to return
        
    Returns:
        List of conversation history entries
    """
    return {
        "total_entries": len(conversation_history),
        "entries": conversation_history[-limit:] if len(conversation_history) > limit else conversation_history
    }

@app.post("/api/chat")
def chat_with_agent(message: dict):
    """
    Chat interface for customers to interact with the agent
    
    Args:
        message: Dict with "content" key containing user message
        
    Returns:
        Agent response
    """
    try:
        user_message = message.get("content", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Parse the user message to extract refund request details
        # Look for patterns like "customer_id", "order_id" in the message
        response_text = f"""
        Hello! I'm the AI Customer Support Agent. I can help you with your refund request.
        
        To process your refund, please provide:
        1. Your Customer ID
        2. Your Order ID
        3. Your reason for the refund
        
        You can send a message like: "I want to refund order ORD-2024-001 from customer CUST001 because the item was damaged"
        """
        
        # Store message in conversation history
        conversation_history.append({
            "type": "chat",
            "role": "user",
            "content": user_message,
            "timestamp": str(datetime.now())
        })
        
        return {
            "role": "assistant",
            "content": response_text,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/api/policy")
def get_refund_policy():
    """Get the refund policy"""
    from tools import get_refund_policy
    return {"policy": get_refund_policy()}

# Import datetime for timestamp
from datetime import datetime

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
