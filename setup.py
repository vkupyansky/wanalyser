import asyncio
from database import setup_database

if __name__ == "__main__":
    asyncio.run(setup_database())
