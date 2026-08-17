from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from auth import current_user
from config import settings
from database import get_db
from schema import PaginationPostResponse, postcreate, postresponse, postupdate

route=APIRouter()

@route.get("",response_model=PaginationPostResponse)
async def getapi_posts(
    db:Annotated[AsyncSession,Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page
):
    count_query = select(func.count()).select_from(models.Post)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    query=select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit)
    result=await db.execute(query)
    retrieved_posts=result.scalars().all()
    has_more= skip + len(retrieved_posts) < total
    return PaginationPostResponse(
        posts = [ postresponse.model_validate(post) for post in retrieved_posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more
    )


@route.post("",response_model=postresponse,status_code=status.HTTP_201_CREATED)
async def post_create(post:postcreate,currentuser:current_user,db:Annotated[AsyncSession,Depends(get_db)]):
    
    # query = select(models.User).where(models.User.id == post.user_id)
    # result = await db.execute(query)
    # user= result.scalars().first()
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
    
    new_post=models.Post(
        title=post.title,content=post.content,author_id=currentuser.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post,attribute_names=["author"])
    return new_post


@route.get("/{post_id}",response_model=postresponse)
async def getapi_epost(post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)
    result= await db.execute(query)
    post = result.scalars().first()
    
    if  not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")
    
    return post


@route.put("/{post_id}",response_model=postresponse)
async def api_update_fpost(post_data:postcreate,currentuser:current_user,post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)
    result= await db.execute(query)
    post = result.scalars().first()
    if  not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")
    
    if currentuser.id != post.author_id:
        # query = select(models.User).where(models.User.id == post_data.user_id)
        # result= await db.execute(query)
        # retrived_user = result.scalars().first()
        # if not retrived_user:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User Not Found")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to update this post")
        
    post.title=post_data.title
    post.content=post_data.content
    # post.author_id=post_data.id
    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post


@route.patch("/{post_id}",response_model=postresponse)
async def api_update_post(post_data:postupdate,currentuser:current_user,post_id:int,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)
    result= await db.execute(query)
    post = result.scalars().first()
    if  not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")
    
    if currentuser.id != post.author_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to update this post")
            
    
    update_post = post_data.model_dump(exclude_unset=True)
    
    for fieldkey,fieldvalue in update_post.items():
        
        setattr(post,fieldkey,fieldvalue)
    
    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post


@route.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_post(post_id:int,currentuser:current_user,db:Annotated[AsyncSession,Depends(get_db)]):
    query = select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)
    result= await db.execute(query)
    post = result.scalars().first()
    if  not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")
    
    if currentuser.id != post.author_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to delete this post")
        
    await db.delete(post)
    await db.commit()
    # return {"status":"post deleted"}