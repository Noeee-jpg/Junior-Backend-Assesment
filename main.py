import logging
from fastapi import FastAPI
from config import engine
import model
from router import router

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,  # Set ke INFO untuk menangkap pesan level INFO
    format='%(asctime)s - %(levelname)s - %(message)s'
)

model.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)
