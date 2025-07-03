# -*- coding: utf-8 -*-
# @Time  : 2025/06/29 22:54
# @Author: masonsxu
# @File  : main.py
# @Desc  : Main entry point for the LingShu application


from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlmodel import Session, select

from app.application.channel_processor import ChannelProcessor
from app.infrastructure.database import create_db_and_tables, get_session
from app.domain.models.channel import ChannelModel

app = APIRouter()

# Initialize the channel processor



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
    channel_processor = ChannelProcessor()
    result = await channel_processor.process_message(channel, message)
    return result
