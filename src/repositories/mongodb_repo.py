# Connect and query Mongo DB
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from src.core.cache import cache 

async def get_aps_collection(mongo_uri: str):
    """Creates a client and returns the specific collection on-demand."""
    client = AsyncIOMotorClient(mongo_uri)
    db = client["test"]
    return db.get_collection("aps_tokens")

async def get_aps_token(mongo_uri: str, autodesk_id: str) -> Optional[Dict]:
    """
    Retrieve the APS token document for the given Autodesk ID.
    Caches the result for 5 minutes.
    """
    # 1. Try to fetch the result from the cache first
    cached_token = await cache.get(f"aps_token:{autodesk_id}")
    if cached_token:
        logging.info(f"Cache HIT for aps_token:{autodesk_id}")
        return cached_token

    # 2. If not in cache, query the database
    logging.info(f"Cache MISS for aps_token:{autodesk_id}")
    try:
        aps_collection = await get_aps_collection(mongo_uri)
        doc = await aps_collection.find_one({"autodesk_id": autodesk_id})
        
        # 3. Store the result in the cache before returning
        if doc:
            await cache.set(f"aps_token:{autodesk_id}", doc)
        return doc
    except Exception as e:
        logging.error(f"Error fetching APS token for {autodesk_id}: {e}")
        return None

async def upsert_aps_token(mongo_uri: str, token_doc: Dict) -> bool:
    """
    Insert or update the APS token document based on autodesk_id
    and update the cache.
    """
    autodesk_id = token_doc.get("autodesk_id")
    if not autodesk_id:
        logging.error("autodesk_id missing from token document.")
        return False
        
    try:
        aps_collection = await get_aps_collection(mongo_uri)
        # 1. Upsert the document in the database
        await aps_collection.update_one(
            {"autodesk_id": autodesk_id},
            {"$set": token_doc},
            upsert=True
        )
        
        # 2. Update the cache with the new document
        await cache.set(f"aps_token:{autodesk_id}", token_doc)
        logging.info(f"Successfully upserted and cached token for {autodesk_id}")
        return True
    except Exception as e:
        logging.error(f"Error upserting APS token for {autodesk_id}: {e}")
        # 3. Invalidate cache on error to prevent stale data
        await cache.delete(f"aps_token:{autodesk_id}")
        return False