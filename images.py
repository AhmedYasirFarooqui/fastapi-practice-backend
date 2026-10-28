from dotenv import load_dotenv
from imagekitio import AsyncImageKit
import os

load_dotenv()

imagekit = AsyncImageKit(
    private_key=os.environ["IMAGEKIT_PRIVATE_KEY"]
)