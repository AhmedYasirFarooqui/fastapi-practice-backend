from fastapi import FastAPI, Form, HTTPException, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from db import PostModel
from sqlalchemy import select
from images import imagekit
from imagekitio import AsyncImageKit
from fastapi import FastAPI, UploadFile, File
import os
import uuid


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    await PostModel.create_db_and_tables()
    yield
    await imagekit.close()


app = FastAPI(lifespan=lifespan)


@app.post("/upload/", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(PostModel.get_async_session),
):
    # Step 1: Validate uploaded file
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "video/mp4",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Step 2: Determine whether file is photo or video
    file_type = "video" if file.content_type.startswith("video/") else "photo"

    file_name = os.path.basename((file.filename or "upload").replace("\\", "/"))

    # Step 3: Upload file to ImageKit
    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        upload_response = await imagekit.files.upload(
            file=file_content,
            file_name=file_name,
            folder="/posts",
            use_unique_file_name=True,
        )

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ImageKit upload failed: {str(e)}")

    finally:
        await file.close()

    # Step 4: Create SQLAlchemy database object
    post = PostModel(
        caption=caption,
        url=upload_response.url,
        file_type=file_type,
        file_name=upload_response.name,
    )

    # Step 5: Save post to database
    try:
        session.add(post)
        await session.commit()
        await session.refresh(post)

    except Exception:
        await session.rollback()
        raise

    # Step 6: Return created post
    return {
        "message": "Post created successfully",
        "post": {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
        },
    }


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(PostModel.get_async_session)):
    result = await session.execute(
        select(PostModel).order_by(PostModel.created_at.desc())
    )
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
            }
        )

    return {"posts": posts_data}


@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(PostModel.get_async_session)):
    try:
        post_uuid = uuid.UUID(post_id)
        
        result = await session.execute(select(PostModel).where(PostModel.id == post_uuid))

        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        await session.delete(post)
        await session.commit()

        return {"success": True,"message": "Post deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

