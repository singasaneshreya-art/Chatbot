import os
import pymongo
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# MongoDB URI and Database Name
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://singasaneshreya_db_user:Smoky2725@cluster0.fxbboxt.mongodb.net/?appName=Cluster0")
db_name = os.getenv("MONGO_DB_NAME", "chatbot_db")

print(f"Connecting to MongoDB database '{db_name}'...")
try:
    # Connect with a timeout of 5 seconds
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    # Force connection check
    client.admin.command('ping')
    print("Connected successfully!")
    
    db = client[db_name]
    orders_col = db["orders"]
    
    # Clear current data in orders collection
    count_before = orders_col.count_documents({})
    print(f"Current document count in 'orders' collection: {count_before}")
    if count_before > 0:
        print("Deleting all documents from 'orders' collection...")
        res = orders_col.delete_many({})
        print(f"Deleted {res.deleted_count} documents.")
    else:
        print("No documents found in 'orders' collection.")
        
    # Import seed data from application service
    from services.mongodb_service import INITIAL_MOCK_ORDERS
    print("Seeding 'orders' collection with initial mock orders...")
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
        
    res_insert = orders_col.insert_many(seed_data)
    print(f"Successfully inserted {len(res_insert.inserted_ids)} seed documents.")
    
    print("\nVerification: Seeded documents:")
    for doc in orders_col.find():
        doc_copy = doc.copy()
        doc_copy.pop("_id", None)
        print(f" - {doc_copy}")
        
    client.close()
    print("\nDatabase reset and seeding completed successfully!")
except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("\nPossible solutions:")
    print("1. If you are running this from a restricted network, make sure your IP is whitelisted in MongoDB Atlas (Network Access).")
    print(f"   Note: This agent's public IP is: 152.59.60.134")
    print("2. Check if your database user credentials (username/password) are correct in your .env file.")
