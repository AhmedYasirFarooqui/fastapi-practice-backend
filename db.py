from collections.abc import AsyncGenerator
import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UUID, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

DATABASE_url = "sqlite+aiosqlite:///./test.db"

#create post database model

class Base(DeclarativeBase):
    pass

class PostModel(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now, nullable=False)

    #create engine

    engine = create_async_engine(DATABASE_url)

    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    async def create_db_and_tables(cls) -> None:
        async with cls.engine.begin() as conn:
            await conn.run_sync(cls.metadata.create_all)

    @classmethod
    async def get_async_session(cls) -> AsyncGenerator[AsyncSession, None]:
        async with cls.async_session_maker() as session:
            yield session