# -*- coding: utf-8 -*-
# @Time  : 2025/06/29 22:54
# @Author: masonsxu
# @File  : main.py
# @Desc  : Main entry point for the LingShu application


from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session
from app.infrastructure.database import get_session
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository
from app.application.channel_processor import ChannelProcessor

app = APIRouter()
channel_processor = ChannelProcessor()

def get_channel_repository(session: Session = Depends(get_session)) -> ChannelRepository:
    return ChannelRepository(session)

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
    channel: ChannelModel,
    repo: ChannelRepository = Depends(get_channel_repository)
) -> ChannelModel:
    existing_channel = repo.get_by_id(channel.id)
    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with ID '{channel.id}' already exists.",
        )
    return repo.add(channel)

@app.get("/channels/", response_model=List[ChannelModel], tags=["Channels"])
async def read_channels(repo: ChannelRepository = Depends(get_channel_repository)):
    return repo.get_all()

@app.get("/channels/{channel_id}", response_model=ChannelModel, tags=["Channels"])
async def get_channel(channel_id: str, repo: ChannelRepository = Depends(get_channel_repository)):
    channel = repo.get_by_id(channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found."
        )
    return channel

@app.post("/channels/{channel_id}/process", tags=["Channels"])
async def process_message_for_channel(
    channel_id: str,
    message: Any = Body(..., description="Message to process"),
    repo: ChannelRepository = Depends(get_channel_repository)
):
    result = await channel_processor.process_message_with_checks(channel_id, message, repo)
    return result
