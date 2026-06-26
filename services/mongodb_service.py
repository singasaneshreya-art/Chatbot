import os
import pymongo
from pymongo.errors import ConnectionFailure, ConfigurationError

client = None
db = None

# Initial mock orders to seed the database if it is empty
INITIAL_MOCK_ORDERS = {
    "ORD-123456": {
        "id": "ORD-123456",
        "status": "Delivered",
        "item": "Wireless Headset",
        "price": "$79.99",
        "eta": None,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
    },
    "ORD-789012": {
        "id": "ORD-789012",
        "status": "Shipped — In Transit",
        "item": "Mechanical Keyboard",
        "price": "$129.99",
        "eta": "2 days",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&q=80"
    },
    "ORD-456789": {
        "id": "ORD-456789",
        "status": "Processing",
        "item": "Ergonomic Mouse",
        "price": "$49.99",
        "eta": "5 days",
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&q=80"
    },
    "ORD-8821": {
        "id": "ORD-8821",
        "status": "Delivered",
        "item": "ErgoCore Pro Series X",
        "model": "Model: 2024-Charcoal",
        "price": "$499.00",
        "badge": "Active Dispute",
        "eta": None,
        "image_url": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=500&q=80"
    }
}

def get_db():
    global client, db
    if db is not None:
        return db
    
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME", "chatbot_db")
    
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set in your .env file")
        
    try:
        # Establish connection with server selection timeout of 5 seconds
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Force connection verification
        client.admin.command('ping')
        db = client[db_name]
        return db
    except (ConnectionFailure, ConfigurationError) as e:
        print(f"MongoDB connection failed: {e}")
        raise e

def seed_db_if_empty():
    try:
        database = get_db()
        orders_col = database["orders"]
        if orders_col.count_documents({}) == 0:
            seed_data = []
            for order_id, details in INITIAL_MOCK_ORDERS.items():
                seed_data.append({
                    "id": order_id,
                    "status": details["status"],
                    "item": details["item"],
                    "price": details["price"],
                    "eta": details.get("eta"),
                    "model": details.get("model"),
                    "badge": details.get("badge"),
                    "customer_name": None,
                    "customer_email": None,
                    "image_url": details.get("image_url")
                })
            orders_col.insert_many(seed_data)
            print("Database was successfully seeded with initial mock orders.")
        else:
            print("Database already contains orders. Seeding skipped.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        # We don't raise here to allow app startup even if seeding fails temporarily (e.g. testing)
