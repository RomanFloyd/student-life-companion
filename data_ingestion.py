import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Configuration ---
MONGO_URI = "mongodb://admin:admin123@localhost:27017/harbour-space?authSource=admin"
DATABASE_NAME = "harbour-space"
JSON_FILE = "knowledge_base_encrypted.json" # The file with hashed passwords

# --- Main Ingestion Logic ---
def ingest_data():
    """
    Connects to MongoDB, clears existing data, and inserts new data
    from the specified JSON file.
    """
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        # The ping command is a simple way to verify the connection.
        client.admin.command('ping')
        print("✅ MongoDB connection successful.")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return

    print(f"Loading data from '{JSON_FILE}'...")
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: The file '{JSON_FILE}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{JSON_FILE}'. Please ensure it is a valid JSON file.")
        return

    # --- Data Transformation and Insertion ---
    
    # Helper function to correctly format the data for MongoDB
    def transform_document(doc):
        # Convert string ObjectIDs to actual ObjectId objects
        if '_id' in doc and isinstance(doc['_id'], dict) and '$oid' in doc['_id']:
            doc['_id'] = ObjectId(doc['_id']['$oid'])
        
        # Convert date strings to datetime objects
        for key, value in doc.items():
            if isinstance(value, dict) and '$date' in value:
                # Assuming ISO 8601 format with 'Z' for UTC
                doc[key] = datetime.fromisoformat(value['$date'].replace('Z', '+00:00'))
            elif isinstance(value, list):
                 # Handle lists of ObjectIds (like in group members)
                 new_list = []
                 for item in value:
                     if isinstance(item, dict) and '$oid' in item:
                         new_list.append(ObjectId(item['$oid']))
                     else:
                         new_list.append(item)
                 doc[key] = new_list
            # Handle single ObjectId references (like group admin or schedule IDs)
            elif isinstance(value, dict) and '$oid' in value:
                 doc[key] = ObjectId(value['$oid'])

        return doc

    collections_to_ingest = {
        "users": data.get("users", []),
        "courses": data.get("courses", []),
        "groups": data.get("groups", []),
        "schedules": data.get("schedules", [])
    }

    for name, documents in collections_to_ingest.items():
        if not documents:
            print(f"⚠️ No documents found for '{name}' collection. Skipping.")
            continue

        collection = db[name]
        
        print(f"\nClearing existing data in '{name}' collection...")
        collection.delete_many({})
        
        print(f"Inserting {len(documents)} documents into '{name}' collection...")
        
        # Transform each document before insertion
        transformed_docs = [transform_document(doc.copy()) for doc in documents]
        
        collection.insert_many(transformed_docs)
        print(f"✅ Successfully inserted data into '{name}'.")

    print("\n🎉 Data ingestion complete!")
    client.close()

if __name__ == "__main__":
    ingest_data()