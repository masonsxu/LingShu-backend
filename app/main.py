from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.channel_router import router as channel_router
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository
from app.infrastructure.database import create_db_and_tables, get_session
from app.infrastructure.logging_config import auto_setup_logging

# 初始化日志配置
auto_setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with next(get_session()) as session:
        repo = ChannelRepository(session)
        example_channel_id = "example-http-to-http"
        if not repo.get_by_id(example_channel_id):
            example_channel_data = {
                "id": example_channel_id,
                "name": "HTTP to HTTP Passthrough",
                "description": (
                    "A simple channel that receives HTTP POST and "
                    "forwards it to another HTTP endpoint."
                ),
                "enabled": True,
                "source": {"type": "http", "path": "/receive/data", "method": "POST"},
                "filters": [
                    {
                        "type": "python_script",
                        "script": (
                            "if 'important_data' in message:\n"
                            "    _passed = True\n"
                            "else:\n"
                            "    _passed = False"
                        ),
                    }
                ],
                "transformers": [
                    {
                        "type": "python_script",
                        "script": (
                            "import datetime\n"
                            "_transformed_message = f'{message} - Processed at "
                            "{datetime.datetime.now()}' "
                        ),
                    }
                ],
                "destinations": [
                    {
                        "type": "http",
                        "url": "https://webhook.site/YOUR_WEBHOOK_URL",
                        "method": "POST",
                        "headers": {"Content-Type": "text/plain"},
                    }
                ],
            }
            example_channel = ChannelModel(**example_channel_data)
            repo.add(example_channel)
    yield


app = FastAPI(
    title="LingShu - Healthcare Data Integration Platform",
    description="A modern, visual platform for healthcare data integration.",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


app.include_router(channel_router)

# 添加根路由
@app.get("/")
async def read_root():
    """根路由"""
    return {"message": "Welcome to LingShu!", "version": "0.1.0"}
