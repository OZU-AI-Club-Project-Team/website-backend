from fastapi import FastAPI
from prisma import Client

from app.db import db
from app.routers import auth as auth_router

app = FastAPI(title="Project Backend", version="1.0.0")

app.include_router(auth_router.router)

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





