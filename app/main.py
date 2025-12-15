
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import db
from app.routers.index import setup_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(title="AI Website Backend", version="1.0.0", lifespan=lifespan)

# Bütün uygulamayı bu metot başlatıyor routers, headers, vs.
setup_app(app)


@app.get("/")
def root():
    return {"message": "API is working!"}


@app.get("/prisma-users")
async def get_prisma_users():
    users = await db.user.find_many()
    return users


@app.get("/ping")
async def ping():
    return {"message": "pong"}
