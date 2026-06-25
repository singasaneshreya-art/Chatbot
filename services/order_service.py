import re
import random

# In-memory mock database of orders
MOCK_ORDERS = {
    "ORD-123456": {
        "id": "ORD-123456",
        "status": "Delivered",
        "item": "Wireless Headset",
        "price": "$79.99",
        "eta": None
    },
    "ORD-789012": {
        "id": "ORD-789012",
        "status": "Shipped — In Transit",
        "item": "Mechanical Keyboard",
        "price": "$129.99",
        "eta": "2 days"
    },
    "ORD-456789": {
        "id": "ORD-456789",
        "status": "Processing",
        "item": "Eronomic Mouse",
        "price": "$49.99",
        "eta": "5 days"
    },
    "ORD-8821": {
        "id": "ORD-8821",
        "status": "Delivered",
        "item": "ErgoCore Pro Series X",
        "model": "Model: 2024-Charcoal",
        "price": "$499.00",
        "badge": "Active Dispute",
        "eta": None
    }
}

ITEMS_POOL = [
    "Gaming Monitor", 
    "USB-C Hub", 
    "Noise Cancelling Headphones", 
    "Laptop Stand", 
    "Mechanical Numpad"
]

STATUS_POOL = ["Processing", "Shipped — In Transit", "Delivered"]

def get_order(order_id: str) -> dict | None:
    """Lookup and return order details by ID, or None if not found."""
    if not order_id:
        return None
    return MOCK_ORDERS.get(order_id.upper())

def extract_order_id(text: str) -> str | None:
    """
    Extracts Order ID from text.
    1. Looks for ORD-XXXX (4 to 6 digits)
    2. Fallback: Looks for a 4 to 6 digit numeric string, checks if ORD-XXXX exists in the store.
    """
    if not text:
        return None
        
    # Case 1: Look for ORD- followed by 4 to 6 digits
    match = re.search(r'\bORD-(\d{4,6})\b', text, re.IGNORECASE)
    if match:
        return f"ORD-{match.group(1)}".upper()
        
    # Case 2: Fallback to 4 to 6 digit number
    numeric_match = re.search(r'\b(\d{4,6})\b', text)
    if numeric_match:
        candidate_id = f"ORD-{numeric_match.group(1)}".upper()
        if candidate_id in MOCK_ORDERS:
            return candidate_id
            
    return None

def create_random_order() -> str:
    """Generates a random Order ID, registers it, and returns the ID."""
    while True:
        digits = "".join(str(random.randint(0, 9)) for _ in range(6))
        new_id = f"ORD-{digits}"
        if new_id not in MOCK_ORDERS:
            break
            
    status = random.choice(STATUS_POOL)
    item = random.choice(ITEMS_POOL)
    price_val = round(random.uniform(15.0, 250.0), 2)
    price = f"${price_val:.2f}"
    
    eta = None
    if status == "Processing":
        eta = f"{random.randint(4, 7)} days"
    elif status == "Shipped — In Transit":
        eta = f"{random.randint(1, 3)} days"
        
    MOCK_ORDERS[new_id] = {
        "id": new_id,
        "status": status,
        "item": item,
        "price": price,
        "eta": eta
    }
    
    return new_id
