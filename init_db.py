"""
Database initialization script
Run this to create tables in your database
"""

import asyncio
from app.core.database import async_engine, Base
from app.models.user import User  # Import to register the model

async def create_tables():
    """Create all tables."""
    async with async_engine.begin() as conn:
        # Drop all tables (for development only)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())