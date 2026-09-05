from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.avatars import AVATARS_DIR, avatar_url_for, save_avatar
from app.database import Base, engine, get_db
from app.connection_manager import manager
from app.models import Message
from app.schemas import AvatarOut, MessageOut
from app.tripcode import (
    MAX_TRIP_PASSWORD_LENGTH,
    compute_trip,
    resolve_identity,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ChatApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"https://.*\.trycloudflare\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/avatars", StaticFiles(directory=AVATARS_DIR), name="avatars")


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/messages", response_model=list[MessageOut])
def list_messages(db: Session = Depends(get_db)):
    messages = db.scalars(select(Message).order_by(Message.created_at)).all()
    return [
        MessageOut(
            id=m.id,
            username=m.username,
            trip=m.trip,
            content=m.content,
            created_at=m.created_at,
            avatar_url=avatar_url_for(m.trip),
        )
        for m in messages
    ]


@app.post("/avatar", response_model=AvatarOut)
async def upload_avatar(
    trip_password: str = Form(...), file: UploadFile = File(...)
):
    if not trip_password:
        raise HTTPException(status_code=400, detail="合言葉が必要です")

    trip = compute_trip(trip_password[:MAX_TRIP_PASSWORD_LENGTH])
    await save_avatar(trip, file)
    return AvatarOut(trip=trip, avatar_url=avatar_url_for(trip))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        join_data = await websocket.receive_json()
        identity = resolve_identity(join_data.get("name", ""))
        manager.register(websocket, identity)
        await websocket.send_json(
            {
                "type": "joined",
                "username": identity.name,
                "trip": identity.trip,
                "avatar_url": avatar_url_for(identity.trip),
            }
        )

        while True:
            data = await websocket.receive_json()
            content = data.get("content", "")

            db = next(get_db())
            message = Message(
                username=identity.name, trip=identity.trip, content=content
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            db.close()

            await manager.broadcast(
                {
                    "type": "message",
                    "id": message.id,
                    "username": message.username,
                    "trip": message.trip,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "avatar_url": avatar_url_for(message.trip),
                }
            )
    except WebSocketDisconnect:
        manager.unregister(websocket)
