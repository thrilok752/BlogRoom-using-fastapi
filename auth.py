import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from config import settings
from database import get_db

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_passoword(plain_password: str,hashed_password: str) -> bool:
    return password_hash.verify(plain_password,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta | None =None) -> str:
    to_enocode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        
    to_enocode.update({"exp":expire})
    
    encode_jwt =jwt.encode(to_enocode,settings.secret_key.get_secret_value(),algorithm=settings.alogrithm)
    
    return encode_jwt

def verify_access_token(token: str) -> str | None:
    try:
        data=jwt.decode(token,settings.secret_key.get_secret_value(),algorithms=[settings.alogrithm],options={"require":["exp","sub"]})
    
    except jwt.InvalidTokenError:
        return None
    
    return data.get("sub")


async def get_current_user(token:Annotated[str,Depends(oauth2_scheme)],db:Annotated[AsyncSession,Depends(get_db)]):
    user_id =verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token or expired token",
            headers={"WWW-Authenticate":"Bearer"}
        )
    try:
        user_id_int = int(user_id)
    except(TypeError,ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate":"Bearer"}
            )
    query = select(models.User).where(models.User.id == user_id_int)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not Found",
            headers={"WWW-Authenticate":"Bearer"})
    
    return user


current_user = Annotated[models.User,Depends(get_current_user)]



def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()