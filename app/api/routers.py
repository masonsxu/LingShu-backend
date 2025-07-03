# -*- coding: utf-8 -*-
# @Time  : 2025/06/29 22:54
# @Author: masonsxu
# @File  : main.py
# @Desc  : Main entry point for the LingShu application


from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core.channel_processor import ChannelProcessor
from app.infrastructure.database import create_db_and_tables, get_session
from app.domain.models.channel import ChannelModel

app = APIRouter()

# Initialize the channel processor
channel_processor = ChannelProcessor()


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    # Add an example channel to the database on startup if it doesn't exist
    with next(get_session()) as session:
        example_channel_id = "example-http-to-http"
        existing_channel = session.get(ChannelModel, example_channel_id)
        if not existing_channel:
            example_channel_data = {
                "id": example_channel_id,
                "name": "HTTP to HTTP Passthrough",
                "description": "A simple channel that receives HTTP POST and forwards it to another HTTP endpoint.",
                "enabled": True,
                "source": {"type": "http", "path": "/receive/data", "method": "POST"},
                "filters": [
                    {
                        "type": "python_script",
                        "script": """# Example filter: only allow messages containing 'important_data'
                                        if 'important_data' in message:
                                            _passed = True
                                        else:
                                            _passed = False
                                    """,
                    }
                ],
                "transformers": [
                    {
                        "type": "python_script",
                        "script": """# Example transformer: add a timestamp to the message
                        import datetime
                        _transformed_message = f"{message} - Processed at {datetime.datetime.now()}"
                        """,
                    }
                ],
                "destinations": [
                    {
                        "type": "http",
                        "url": "https://webhook.site/YOUR_WEBHOOK_URL",  # Replace with a real webhook URL for testing
                        "method": "POST",
                        "headers": {"Content-Type": "text/plain"},
                    }
                ],
            }
            try:
                example_channel = ChannelModel(**example_channel_data)
                session.add(example_channel)
                session.commit()
                session.refresh(example_channel)
                print(f"Loaded example channel: {example_channel.name}")
            except ValidationError as e:
                print(f"Error loading example channel: {e}")
        else:
            print(f"Example channel '{existing_channel.name}' already exists in DB.")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to LingShu!"}


@app.post(
    "/channels/",
    response_model=ChannelModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Channels"],
)
async def create_channel(
    channel: ChannelModel, session: Session = Depends(dependency=get_session)
) -> ChannelModel:
    """Create a new data channel."""
    existing_channel: Any = session.get(ChannelModel, channel.id)
    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with ID '{channel.id}' already exists.",
        )
    session.add(channel)
    session.commit()
    session.refresh(channel)
    return channel


@app.get("/channels/", response_model=List[ChannelModel], tags=["Channels"])
async def read_channels(session: Session = Depends(get_session)):
    """Retrieve all channels."""
    channels = session.exec(select(ChannelModel)).all()
    return channels


@app.get("/channels/{channel_id}", response_model=ChannelModel, tags=["Channels"])
async def get_channel(channel_id: str, session: Session = Depends(get_session)):
    """Retrieve a channel by its ID."""
    channel = session.get(ChannelModel, channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found."
        )
    return channel


@app.post("/channels/{channel_id}/process", tags=["Channels"])
async def process_message_for_channel(
    channel_id: str,
    message: Any,  # Can be any JSON-serializable data
    session: Session = Depends(get_session),
):
    """Simulate processing a message through a specific channel."""
    channel = session.get(ChannelModel, channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found."
        )

    if not channel.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Channel is disabled."
        )

    # Process the message using the ChannelProcessor
    result = await channel_processor.process_message(channel, message)
    return result
