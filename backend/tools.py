import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Data directory path
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

class Database:
    """In-memory database handler for customers and orders"""
    
    def __init__(self):
        self.customers = {}
        self.orders = {}
        self.refund_policy = ""
        self.load_data()
    
    def load_data(self):
        """Load customer, order, and policy data"""
        try:
            # Load customers
            with open(os.path.join(DATA_DIR, 'customers.json'), 'r') as f:
                customers_data = json.load(f)
                for customer in customers_data['customers']:
                    self.customers[customer['customer_id']] = customer
            
            # Load orders
            with open(os.path.join(DATA_DIR, 'orders.json'), 'r') as f:
                orders_data = json.load(f)
                for order in orders_data['orders']:
                    self.orders[order['order_id']] = order
            
            # Load refund policy
            with open(os.path.join(DATA_DIR, 'refund_policy.txt'), 'r') as f:
                self.refund_policy = f.read()
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer information"""
        return self.customers.get(customer_id)
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order information"""
        return self.orders.get(order_id)
    
    def verify_customer_order(self, customer_id: str, order_id: str) -> bool:
        """Verify that order belongs to customer"""
        order = self.get_order(order_id)
        if not order:
            return False
        return order['customer_id'] == customer_id
    
    def get_policy(self) -> str:
        """Get refund policy"""
        return self.refund_policy

# Global database instance
db = Database()

def get_customer_info(customer_id: str) -> Dict:
    """Tool: Get customer information"""
    customer = db.get_customer(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    
    return {
        "found": True,
        "customer_id": customer['customer_id'],
        "name": customer['name'],
        "email": customer['email'],
        "phone": customer['phone'],
        "account_status": customer['account_status'],
        "total_spent": customer['total_spent'],
        "order_count": len(customer['orders'])
    }

def get_order_info(order_id: str) -> Dict:
    """Tool: Get order information"""
    order = db.get_order(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}
    
    return {
        "found": True,
        "order_id": order['order_id'],
        "customer_id": order['customer_id'],
        "order_date": order['order_date'],
        "purchase_amount": order['purchase_amount'],
        "items": order['items'],
        "product_category": order['product_category'],
        "is_final_sale": order['is_final_sale'],
        "days_since_purchase": order['days_since_purchase'],
        "status": order['status']
    }

def verify_order_customer(customer_id: str, order_id: str) -> Dict:
    """Tool: Verify that order belongs to customer"""
    verified = db.verify_customer_order(customer_id, order_id)
    return {
        "verified": verified,
        "customer_id": customer_id,
        "order_id": order_id
    }

def get_refund_policy() -> str:
    """Tool: Get refund policy"""
    return db.get_policy()

# Define tools for the agent
TOOLS = [
    {
        "name": "get_customer_info",
        "description": "Get customer information including account status, total spent, and order history count",
        "function": get_customer_info
    },
    {
        "name": "get_order_info",
        "description": "Get order information including price, category, final sale status, and days since purchase",
        "function": get_order_info
    },
    {
        "name": "verify_order_customer",
        "description": "Verify that a given order belongs to a specific customer",
        "function": verify_order_customer
    },
    {
        "name": "get_refund_policy",
        "description": "Get the complete refund policy document",
        "function": get_refund_policy
    }
]

def execute_tool(tool_name: str, **kwargs) -> str:
    """Execute a tool and return result as string"""
    tool = next((t for t in TOOLS if t["name"] == tool_name), None)
    if not tool:
        return f"Error: Tool {tool_name} not found"
    
    try:
        result = tool["function"](**kwargs)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
