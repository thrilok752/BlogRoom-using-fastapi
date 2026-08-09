from typing import Annotated
from datetime import timedelta,datetime,UTC
from fastapi import HTTPException,status,Depends,APIRouter,UploadFile,File,Form,Query
from fastapi.security import OAuth2PasswordRequestForm
from schema import (
    postresponse,UserPublic,UserPrivate,
    UserCreate,UserUpdate,Token,PaginationPostResponse,
    ForgotPasswordRequest,ResetPasswordRequest,ChangePasswordRequest)
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from sqlalchemy import select,func,delete
from auth import (
    create_access_token,hash_password,
    verify_passoword,current_user,hash_reset_token,generate_reset_token)
from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from config import settings
from image_utils import delete_profile_image,process_profile_image,save_image
import models
from email_utils import send_email,send_password_reset_email

route=APIRouter()

@route.post("",response_model=UserPrivate,status_code=status.HTTP_201_CREATED)       
async def user_create(
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[AsyncSession,Depends(get_db)],
    image: UploadFile | None = File(None),
    ):
    
    user = UserCreate(username=username,email=email,password=password)
    u_query=select(models.User).where(func.lower(models.User.username)==user.username.lower())
    em_query=select(models.User).where(func.lower(models.User.email)==user.email.lower())
    u_result=await db.execute(u_query)
    em_result=await db.execute(em_query)
    existing_user=u_result.scalars().first()
    existing_email=em_result.scalars().first()
    if existing_user:
        raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User Already exists")
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email Already exists")
    
    filename=None
    
    if image is not None:
            filename = await save_image(image)
  
    new_user=models.User(username=user.username,email=user.email,password_hash=hash_password(user.password),image_file=filename)
    
    
        
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@route.post("/token",response_model=Token)

async def login_for_accesss_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.User).where(func.lower(models.User.email) == form_data.username.lower())
    result = await db.execute(query)
    user = result.scalars().first()
    if not user or not verify_passoword(form_data.password,user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="incorrect email or password",headers={"WWW-Authenticate":"Bearer"})
    token_expiry =timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub":str(user.id)},expires_delta=token_expiry)
    
    return Token(access_token=access_token,token_type="bearer")


@route.get("/me",response_model=UserPrivate)
async def get_current_user(user:current_user):
    return user


@route.get("/{user_id}",response_model=UserPublic)
async def getapi_user(user_id: int,db:Annotated[AsyncSession,Depends(get_db)]):
    
    query = select(models.User).where(models.User.id == user_id)
    result= await db.execute(query)
    retrived_user = result.scalars().first()
    if retrived_user:
        return retrived_user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")


@route.patch("/{user_id}",response_model=UserPrivate)
async def api_update_user(user_data:UserUpdate,currentuser:current_user,user_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    
    if user_id != currentuser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to update this user")
    
    query = select(models.User).where(models.User.id == user_id)
    result= await db.execute(query)
    user = result.scalars().first()
    
    if  not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
    
    if user_data.username is not None and user_data.username.lower() != user.username.lower():
        u_query=select(models.User).where(func.lower(models.User.username)==user_data.username.lower())
        u_result=await db.execute(u_query)
        existing_user=u_result.scalars().first()
        if existing_user:
                raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User Already exists")
        
    if user_data.email is not None and user_data.email.lower() != user.email.lower():
            em_query=select(models.User).where(func.lower(models.User.email)==user_data.email.lower())
            em_result=await db.execute(em_query)
            existing_email=em_result.scalars().first()
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email Already exists")
        
    
    update_post = user_data.model_dump(exclude_unset=True)
    
    for fieldkey,fieldvalue in update_post.items():
        
        setattr(user,fieldkey,fieldvalue)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@route.patch("/{user_id}/profile_image",response_model=UserPrivate)
async def api_update_picture(currentuser:current_user,user_id:int,db:Annotated[AsyncSession,Depends(get_db)],image: UploadFile = File(None)):
    
    if user_id != currentuser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to update picture")
    
    oldfile = currentuser.image_file
    currentuser.image_file = await save_image(image)
    
    await db.commit()
    await db.refresh(currentuser)
    
    if oldfile:
        await delete_profile_image(oldfile)
    
    return currentuser




@route.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_user(user_id:int,currentuser:current_user,db:Annotated[AsyncSession,Depends(get_db)]):
    if user_id != currentuser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to delete this user")
    
    query = select(models.User).where(models.User.id == user_id)
    result= await db.execute(query)
    user = result.scalars().first()
    
    if  not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
    
    oldfile = currentuser.image_file
    await db.delete(user)
    await db.commit()
    
    if oldfile:
        await delete_profile_image(oldfile)
    
    
@route.delete("/{user_id}/profile_image",response_model=UserPrivate)
async def api_delete_picturer(user_id:int,currentuser:current_user,db:Annotated[AsyncSession,Depends(get_db)]):
    if user_id != currentuser.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to delete this user picture")
    
    oldfile = currentuser.image_file
    
    if oldfile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,detail="no profile picture to delete",
        )
    currentuser.image_file = None
    await db.commit()
    await db.refresh(currentuser)
    await delete_profile_image(oldfile)
    
    return currentuser
    
@route.get("/{user_id}/posts",response_model=PaginationPostResponse)
async def getuserapi_posts(
    user_id: int,
    db:Annotated[AsyncSession,Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page):
    
    userquery=select(models.User).where(models.User.id == user_id)
    result=await db.execute(userquery)
    user=result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
    
    count_query = select(func.count()).select_from(models.Post).where(models.Post.author_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.author_id == user_id).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    retrieved_posts= result.scalars().all()
    has_more= skip + len(retrieved_posts) < total
    return PaginationPostResponse(
            posts = [ postresponse.model_validate(post) for post in retrieved_posts],
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more)

@route.post("/forgot-password",status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(request:ForgotPasswordRequest,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.User).where(models.User.email == request.email)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        return
    token = generate_reset_token()
    token_hash = hash_reset_token(token)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)
    token_storage=models.PasswordResetToken(user_id= user.id,token_hash=token_hash,expire_at=expires_at)
    db.add(token_storage)
    await db.commit()
    await send_password_reset_email(to_email=user.email,username=user.username,token=token)
    return
    
@route.post("/reset-password")
async def reset_password(request:ResetPasswordRequest,db:Annotated[AsyncSession,Depends(get_db)]):
    token_hash = hash_reset_token(request.token)
    query = select(models.PasswordResetToken).options(selectinload(models.PasswordResetToken.user)).where(models.PasswordResetToken.token_hash == token_hash)
    result = await db.execute(query)
    htoken = result.scalars().first()
    if not htoken:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid Reset Token")
    # if htoken.expire_at.replace(tzinfo=UTC) < datetime.now(UTC):
    if htoken.expire_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Reset Token is Expired")
    user=htoken.user
    user.password_hash = hash_password(request.new_password)
    user_token_query = delete(models.PasswordResetToken).where(models.PasswordResetToken.user_id == user.id)
    await db.execute(user_token_query)
    await db.commit()
    
@route.patch("/me/password")
async def change_password(request:ChangePasswordRequest,currentuser:current_user,db:Annotated[AsyncSession,Depends(get_db)]):
    new_password_hash=hash_password(request.new_password)
    if not verify_passoword(request.current_password,currentuser.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="current password is incorrect")
    currentuser.password_hash = new_password_hash
    await db.commit()
    
    
    




