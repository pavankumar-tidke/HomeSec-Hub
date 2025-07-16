from motor.motor_asyncio import AsyncIOMotorClient
from ..config import config
from urllib.parse import urlparse

uri = config.MONGO_URI
client = AsyncIOMotorClient(uri)

# Extract database name from URI, fallback to 'security' if not present
parsed = urlparse(uri)
if parsed.path and len(parsed.path) > 1:
    db_name = parsed.path[1:]
else:
    db_name = 'security'

db = client[db_name] 