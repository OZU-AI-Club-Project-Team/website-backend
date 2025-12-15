from fastapi import HTTPException, status
from app.db import db


async def mark_read(application_id: int):
    app = await db.application.find_unique(where={"id": application_id})
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    await db.application.update(where={"id": application_id}, data={"isRead": True})
    return {"id": application_id, "isRead": True}
