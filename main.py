import math
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as starlette_httpexception

import models
from config import settings
from database import engine, get_db
from routers import posts, users


@asynccontextmanager
async def lifespan(app:FastAPI):
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    
    await engine.dispose()

app=FastAPI(lifespan=lifespan)

app.mount("/static",StaticFiles(directory="static"),name='static')
# app.mount("/media",StaticFiles(directory="media"),name='media')
templates=Jinja2Templates(directory="templates")

app.include_router(users.route,prefix="/api/users",tags=["users"])
app.include_router(posts.route,prefix="/api/posts",tags=["posts"])


## Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"

    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response

@app.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "healthy"}


@app.get("/login",include_in_schema=False,name="Login")
async def login(requests:Request):
    return templates.TemplateResponse(requests,"auth/login.html")
@app.get("/register",include_in_schema=False,name="Register")
async def register(requests:Request):
    return templates.TemplateResponse(requests,"auth/register.html")
@app.get("/logout",include_in_schema=False,name="Logout")
async def logout(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/logout.html",
    )
@app.get("/Profile",include_in_schema=False,name="Profile")
async def profile(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user/profile.html",
    )
    
@app.get("/password-reset",include_in_schema=False,name="PasswordReset")
async def password_reset(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_reset.html",
    )

@app.get("/password-reset-done",include_in_schema=False,name="PasswordResetDone")
async def password_reset_done(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_reset_done.html",
    )
    
@app.get("/reset-password",include_in_schema=False,name="PasswordResetConfimr")
async def password_reset_confirm(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_reset_confirm.html",
    )

@app.get("/password-reset-complete",include_in_schema=False,name="PasswordResetComplete")
async def password_reset_complete(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_reset_complete.html",
    )
    
@app.get("/password-change",include_in_schema=False,name="PasswordChange")
async def password_change(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_change.html",
    )

@app.get("/password-change-done",include_in_schema=False,name="PasswordChangeDone")
async def password_change_done(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="password/password_change_done.html",
    )
    
@app.get("/",include_in_schema=False,name="Home")
@app.get("/posts",include_in_schema=False,name="Posts")
async def home(requests:Request,db:Annotated[AsyncSession,Depends(get_db)],page:Annotated[int,Query(ge=1)]=1):
    
    count_query = select(func.count()).select_from(models.Post)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    limit = settings.posts_per_page
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit)
    query=select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit)
    result=await db.execute(query)
    posts=result.scalars().all()
    # has_more = len(posts) < total
    return templates.TemplateResponse(requests,"mainpage/home.html",{"posts":posts,"total_pages":total_pages,"total":total,"page":page})


@app.get("/about",include_in_schema=False)
def about(requests:Request):
    return templates.TemplateResponse(requests,"mainpage/about.html")


@app.get("/posts/newpost",include_in_schema=False,name="PostForm")

async def create_post_page(requests:Request):
    
    return templates.TemplateResponse(requests,"posts/post_form.html",{"post":None}) 


@app.get("/posts/{post_id}",include_in_schema=False,name="postdetails")
async def get_post(requests:Request,post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id== post_id)
    result=await db.execute(query)
    post=result.scalars().first()
    
    if post:
        return templates.TemplateResponse(requests,"posts/post_detail.html",{"postdetail":post})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")


@app.get("/users/{user_id}/posts",include_in_schema=False,name="userposts")
async def get_user_posts(requests:Request,user_id:int,db:Annotated[AsyncSession,Depends(get_db)],page:Annotated[int,Query(ge=1)]=1):
    query = select(models.User).where(models.User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
    
    
    count_query = select(func.count()).select_from(models.Post).where(models.Post.author_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    limit = settings.posts_per_page
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit)
    
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.author_id == user_id).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return templates.TemplateResponse(requests,"posts/user_posts.html",{"posts":posts,"username":user.username,"total_pages":total_pages,"total":total,"page":page})


@app.get("/posts/{post_id}/postedit_form",include_in_schema=False,name="EditForm")

async def update_post_page(requests:Request,post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):

    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id== post_id)
    result=await db.execute(query)
    post=result.scalars().first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")
    
    return templates.TemplateResponse(requests,"posts/post_form.html",{"post":post})


@app.get("/posts/{post_id}/delete_confirm",include_in_schema=False,name="DeleteConfirm")

async def delete_confirm_page(requests:Request,post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id== post_id)
    result=await db.execute(query)
    post=result.scalars().first()
    
    if post:
        return templates.TemplateResponse(requests,"posts/post_confirm_delete.html",{"post_data":post})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")

  
@app.exception_handler(starlette_httpexception)
async def starlette_handler(requests:Request,exc:starlette_httpexception):
    
    if requests.url.path.startswith("/api"):
        return await http_exception_handler(requests,exc)
    
    message=exc.detail if exc.detail else "an error occured.please check your request and try again."

    return templates.TemplateResponse(
        requests,"error.html",
        {
            "status_code":exc.status_code,
            "title":exc.status_code,
            "message":message,
        },
        status_code=exc.status_code)
    
    
@app.exception_handler(RequestValidationError)
async def req_valid_error(requests:Request,exc:RequestValidationError):
    
    if requests.url.path.startswith("/api"):
        return await request_validation_exception_handler(requests,exc)
    return templates.TemplateResponse(
        requests,"error.html",
        {
            "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message":"The request is invalid"
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )
