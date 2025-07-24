# Connect and query PostgreSQL DB
import logging
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.core.cache import cache 

engine = create_async_engine(
    settings.POSTGRES_DSN,
    echo=False,
)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_user_by_phone(phone_number: str) -> Optional[Dict]:
    """
    Fetch a user record by phone number from the 'users' table.
    Caches the result for 5 minutes.
    Returns a dict with keys: autodesk_id, first_name, hub_id.
    """
    # 1. Try to fetch the result from the cache first
    cached_user = await cache.get(f"user_phone:{phone_number}")
    if cached_user:
        logging.info(f"Cache HIT for user_phone:{phone_number}")
        return cached_user

    # 2. If not in cache, query the database
    logging.info(f"Cache MISS for user_phone:{phone_number}")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("""
                SELECT autodesk_id, first_name, hub_id
                FROM users
                WHERE phone_number = :phone
                LIMIT 1
                """),
                {"phone": phone_number}
            )
            row = result.fetchone()
            if row:
                user_data = {
                    "autodesk_id": row[0],
                    "first_name": row[1],
                    "hub_id": row[2],
                    "phone_number": phone_number
                }
                # 3. Store the result in the cache before returning
                await cache.set(f"user_phone:{phone_number}", user_data)
                return user_data
            return None
        except Exception as e:
            logging.error(f"Error fetching user by phone {phone_number}: {e}")
            return None

async def get_company_config(hub_id: str) -> Optional[Dict]:
    """
    Fetch company configuration by hub_id from the 'company_configs' table.
    Caches the result for 5 minutes.
    Returns a dict with keys: mongodb_uri, client_id, client_secret.
    """
    # 1. Try to fetch the result from the cache first
    cached_config = await cache.get(f"company_config:{hub_id}")
    if cached_config:
        logging.info(f"Cache HIT for company_config:{hub_id}")
        return cached_config

    # 2. If not in cache, query the database
    logging.info(f"Cache MISS for company_config:{hub_id}")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("""
                SELECT mongodb_uri, client_id, client_secret
                FROM company_configs
                WHERE hub_id = :hub_id
                LIMIT 1
                """),
                {"hub_id": str(hub_id)}
            )
            row = result.fetchone()
            if row:
                config_data = {
                    "mongodb_uri": row[0],
                    "client_id": row[1],
                    "client_secret": row[2],
                }
                # 3. Store the result in the cache before returning
                await cache.set(f"company_config:{hub_id}", config_data)
                return config_data
            return None
        except Exception as e:
            logging.error(f"Error fetching company config for hub_id {hub_id}: {e}")
            return None