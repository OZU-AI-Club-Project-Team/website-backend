from fastapi import FastAPI

from app.db import db
from app.routers.index import setup_app

app = FastAPI(title="AI Website Backend", version="1.0.0")

# Bütün uygulamayı bu metot başlatıyor routers, headers, vs.
setup_app(app)


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


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
