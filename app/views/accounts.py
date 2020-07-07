  
from typing import List
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from fastapi import FastAPI, Request, Depends,Response, HTTPException, status, APIRouter
from fastapi.responses import HTMLResponse,JSONResponse
from app.db.mongodb import get_mongo_connection,get_nosql_db,close_mongo_connection,AsyncIOMotorClient
import logging
from app.core import settings
from pydantic import BaseModel
from app.utils.accounts import (
    create_access_token,
    authenticate_user,
    create_user,
    get_current_active_user
)
from datetime import datetime, timedelta

from app.models.accounts import(
    UserInDB,
    User
)
from pymongo.errors import (
    DuplicateKeyError,
    AutoReconnect,
    CollectionInvalid
    )
from app.serializers.account_serializer import(
    Token,
    TokenData,
    LoginRequest,
    RegisterRequest
)

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    await get_mongo_connection()
    try:
        client = await get_nosql_db()
        db = client[settings.MONGODB_NAME]
        collection = db["user"]
        await collection.create_index("username",name="username",unique=True)

    except AutoReconnect as e:
        logging.error(e)
        pass

    except CollectionInvalid as e:
        logging.info(e)
        pass



@router.get("/")
async def get():
    return HTMLResponse("Hello World")


@router.post('/register')
async def register_user(request:RegisterRequest,client:AsyncIOMotorClient=Depends(get_nosql_db)):
    try:
        collection = client[settings.MONGODB_NAME]["user"]
        user = create_user(request)
        dbuser = UserInDB(**user.dict())
        response  = await collection.insert_one(dbuser.dict())
        return {
            "user_id":str(response.inserted_id)
        }
    except DuplicateKeyError as e:
        print(e)
        return JSONResponse(status_code=400,content={
            "user_id":"user_alreay exists"
        })


@router.post("/token", response_model=Token)
async def login_for_access_token(request:LoginRequest):
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRY))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
