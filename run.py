import os
import logging
import uvicorn
from fastapi import FastAPI
from app.whatsapp import router as whatsapp_router

logging.basicConfig(level=logging.INFO)

api = FastAPI()
api.include_router(whatsapp_router)


@api.get("/")
def health_check():
    return "Bot is active!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run(api, host="0.0.0.0", port=port)
