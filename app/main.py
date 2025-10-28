from fastapi import FastAPI
import logging

from app.auth.router import router as auth_router
from app.routers.friendship_router import router as friendship_router
from app.routers.chat_router import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth_router)
app.include_router(friendship_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"message": "Qasynda API is running"}
