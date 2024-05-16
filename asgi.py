import os
import uvicorn

from api.app import create_app
from api.config import settings

api = create_app(settings)

if __name__ == "__main__":
    # TODO: remove it later
    old_db_path = 'database2.db'
    if os.path.exists(old_db_path):
        os.remove(old_db_path)
    uvicorn.run("asgi:api", host="0.0.0.0", port=8080, reload=True)
