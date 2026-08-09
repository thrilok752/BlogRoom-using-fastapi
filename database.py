from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from config import settings


from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine,AsyncSession



# db_url="sqlite+aiosqlite:///./blog.db"
db_url=settings.database_url


# engine =create_async_engine(db_url,connect_args={"check_same_thread":False})
engine =create_async_engine(db_url)

async_sessionlocal=async_sessionmaker(engine,class_=AsyncSession,expire_on_commit=False)

class Base(DeclarativeBase):
    pass






        
        
async def get_db():
    
    async with  async_sessionlocal() as session:
        
        yield session
