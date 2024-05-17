import os
import uvicorn

from api.app import create_app
from api.config import settings

# TODO: remove it later
old_db_path = 'database2.db'
if os.path.exists(old_db_path):
    os.remove(old_db_path)
    
api = create_app(settings)

if __name__ == "__main__":
    uvicorn.run("asgi:api", host="0.0.0.0", port=8001, reload=True)
