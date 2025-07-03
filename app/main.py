# -*- coding: utf-8 -*-
# @Time  : 2025/07/03 17:30
# @Author: masonsxu
# @File  : main.py
# @Desc  : Main application assembly

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database import create_db_and_tables, get_session
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository

from app.api.routers import app as api_router

app = FastAPI(
    title="LingShu - Healthcare Data Integration Platform",
    description="A modern, visual platform for healthcare data integration.",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    # 插入示例数据
    with next(get_session()) as session:
        repo = ChannelRepository(session)
        example_channel_id = "example-http-to-http"
        if not repo.get_by_id(example_channel_id):
            example_channel_data = {
                "id": example_channel_id,
                "name": "HTTP to HTTP Passthrough",
                "description": "A simple channel that receives HTTP POST and forwards it to another HTTP endpoint.",
                "enabled": True,
                "source": {"type": "http", "path": "/receive/data", "method": "POST"},
                "filters": [
                    {
                        "type": "python_script",
                        "script": """if 'important_data' in message:\n    _passed = True\nelse:\n    _passed = False""",
                    }
                ],
                "transformers": [
                    {
                        "type": "python_script",
                        "script": """import datetime\n_transformed_message = f'{message} - Processed at {datetime.datetime.now()}' """,
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

app.include_router(api_router)
