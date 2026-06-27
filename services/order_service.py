import re
import random
import os

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

PRODUCT_IMAGES = {
    "Wireless Headset": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80",
    "Mechanical Keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&q=80",
    "Ergonomic Mouse": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&q=80",
    "ErgoCore Pro Series X": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=500&q=80",
    "Gaming Monitor": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&q=80",
    "USB-C Hub": "https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=500&q=80",
    "Noise Cancelling Headphones": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&q=80",
    "Laptop Stand": "https://images.unsplash.com/photo-1585776245991-cf89dd7fc73a?w=500&q=80",
    "Mechanical Numpad": "https://images.unsplash.com/photo-1595225476474-87563907a212?w=500&q=80"
}


from services.mongodb_service import get_db

def get_order(order_id: str) -> dict | None:
    """Lookup and return order details by ID, or None if not found."""
    if not order_id:
        return None
    try:
        db = get_db()
        order = db.orders.find_one({"id": order_id.upper()})
        if order:
            # Convert ObjectId to string to avoid serialization issues
            order["_id"] = str(order["_id"])
            return order
    except Exception as e:
        if os.getenv('TESTING') != 'true':
            print(f"Error fetching order from MongoDB: {e}")
        # Fall back to in-memory MOCK_ORDERS for safety/testing
        return MOCK_ORDERS.get(order_id.upper())
    return None

def update_order_customer(order_id: str, name: str, email: str) -> dict | None:
    """Update customer name and email on the order document in MongoDB."""
    if not order_id:
        return None
    try:
        db = get_db()
        db.orders.update_one(
            {"id": order_id.upper()},
            {"$set": {"customer_name": name, "customer_email": email}}
        )
        return get_order(order_id)
    except Exception as e:
        if os.getenv('TESTING') != 'true':
            print(f"Error updating order customer details in MongoDB: {e}")
        # Fallback update in-memory
        if order_id.upper() in MOCK_ORDERS:
            MOCK_ORDERS[order_id.upper()]["customer_name"] = name
            MOCK_ORDERS[order_id.upper()]["customer_email"] = email
            return MOCK_ORDERS[order_id.upper()]
    return None

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
        if get_order(candidate_id) is not None:
            return candidate_id
            
    return None

def create_random_order() -> str:
    """Generates a random Order ID, registers it, and returns the ID."""
    db = None
    try:
        db = get_db()
    except Exception as e:
        if os.getenv('TESTING') != 'true':
            print(f"Warning: MongoDB not available for generating unique ID check, using fallback: {e}")

    while True:
        digits = "".join(str(random.randint(0, 9)) for _ in range(6))
        new_id = f"ORD-{digits}"
        
        # Check uniqueness in DB first, then in fallback MOCK_ORDERS
        if db is not None:
            if db.orders.find_one({"id": new_id}) is None:
                break
        else:
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
        
    order_data = {
        "id": new_id,
        "status": status,
        "item": item,
        "price": price,
        "eta": eta,
        "customer_name": None,
        "customer_email": None,
        "image_url": PRODUCT_IMAGES.get(item, "https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=500&q=80")
    }
    
    if db is not None:
        try:
            db.orders.insert_one(order_data)
            # Remove MongoDB internal _id object for return / return string ID
            order_data.pop("_id", None)
        except Exception as e:
            if os.getenv('TESTING') != 'true':
                print(f"Error inserting random order in MongoDB: {e}")
            MOCK_ORDERS[new_id] = order_data
    else:
        MOCK_ORDERS[new_id] = order_data
        
    return new_id
