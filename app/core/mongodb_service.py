"""
MongoDB configuration and operations for storing ingest request metadata
"""
import os
from datetime import datetime
from typing import Optional, List, Dict
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import ssl

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rag_metadata")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ingest_requests")

try:
    # Create MongoDB client with SSL options for MongoDB Atlas
    client_kwargs = {}
    
    # If using MongoDB Atlas (mongodb+srv protocol), handle SSL
    if "mongodb+srv" in MONGODB_URL:
        client_kwargs = {
            "ssl": True,
            "tlsAllowInvalidCertificates": True,  # For development/testing only
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 10000
        }
    
    client = MongoClient(MONGODB_URL, **client_kwargs)
    # Test connection
    client.admin.command('ping')
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Create index for request_id for faster queries
    collection.create_index("request_id", unique=True)
    collection.create_index("document_name")
    collection.create_index("created_at")
    
    print("✅ Connected to MongoDB successfully")
except PyMongoError as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Make sure MongoDB is running. You can start it with: mongod")
    client = None
    db = None
    collection = None


class MongoDBService:
    """Service to manage ingest request records in MongoDB"""
    
    @staticmethod
    def insert_ingest_record(
        request_id: str,
        document_name: str,
        file_size: int,
        total_chunks: int,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Dict:
        """Insert a new ingest request record into MongoDB"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            record = {
                "request_id": request_id,
                "document_name": document_name,
                "file_size": file_size,
                "total_chunks": total_chunks,
                "created_at": datetime.utcnow(),
                "status": status,
                "error_message": error_message
            }
            result = collection.insert_one(record)
            record["_id"] = str(result.inserted_id)
            return record
        except PyMongoError as e:
            raise Exception(f"Failed to insert record: {str(e)}")
    
    @staticmethod
    def get_ingest_record(request_id: str) -> Optional[Dict]:
        """Get a specific ingest request record by request_id"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            record = collection.find_one({"request_id": request_id})
            if record:
                record["_id"] = str(record["_id"])
            return record
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve record: {str(e)}")
    
    @staticmethod
    def get_all_ingest_records(limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all ingest request records with pagination"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            records = list(
                collection.find()
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            for record in records:
                record["_id"] = str(record["_id"])
            return records
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve records: {str(e)}")
    
    @staticmethod
    def get_records_by_document(document_name: str) -> List[Dict]:
        """Get all ingest records for a specific document"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            records = list(
                collection.find({"document_name": document_name})
                .sort("created_at", -1)
            )
            for record in records:
                record["_id"] = str(record["_id"])
            return records
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve records: {str(e)}")
    
    @staticmethod
    def update_ingest_record(
        request_id: str,
        status: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict]:
        """Update an ingest request record"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            update_data = {}
            if status:
                update_data["status"] = status
            if error_message:
                update_data["error_message"] = error_message
            
            result = collection.find_one_and_update(
                {"request_id": request_id},
                {"$set": update_data},
                return_document=True
            )
            if result:
                result["_id"] = str(result["_id"])
            return result
        except PyMongoError as e:
            raise Exception(f"Failed to update record: {str(e)}")
    
    @staticmethod
    def delete_ingest_record(request_id: str) -> bool:
        """Delete an ingest request record"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            result = collection.delete_one({"request_id": request_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            raise Exception(f"Failed to delete record: {str(e)}")
    
    @staticmethod
    def get_statistics() -> Dict:
        """Get statistics about ingested documents"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            total_requests = collection.count_documents({})
            
            # Get total chunks using aggregation
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_chunks": {"$sum": "$total_chunks"},
                        "total_size": {"$sum": "$file_size"}
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            
            if result:
                total_chunks = result[0]["total_chunks"]
                total_size = result[0]["total_size"]
            else:
                total_chunks = 0
                total_size = 0
            
            return {
                "total_requests": total_requests,
                "total_chunks": total_chunks,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "average_chunks_per_document": (
                    total_chunks // total_requests if total_requests > 0 else 0
                ),
                "average_file_size_kb": (
                    round(total_size / total_requests / 1024, 2) if total_requests > 0 else 0
                )
            }
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve statistics: {str(e)}")
    
    @staticmethod
    def get_records_by_date_range(start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get ingest records within a date range"""
        if collection is None:
            raise Exception("MongoDB connection not available")
        
        try:
            records = list(
                collection.find({
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }).sort("created_at", -1)
            )
            for record in records:
                record["_id"] = str(record["_id"])
            return records
        except PyMongoError as e:
            raise Exception(f"Failed to retrieve records: {str(e)}")
