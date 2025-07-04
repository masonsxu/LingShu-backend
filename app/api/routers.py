from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import Session

from app.application.channel_processor import ChannelProcessor
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository
from app.infrastructure.database import get_session

app = APIRouter()
channel_processor = ChannelProcessor()


def get_channel_repository(session: Session = Depends(get_session)) -> ChannelRepository:
    """获取通道仓储实例.

    参数：
        session: 数据库会话对象.

    返回：
        通道仓储实例.
    """
    return ChannelRepository(session)


@app.get("/", tags=["Root"])
async def read_root():
    """根路由.

    返回：
        欢迎消息.
    """
    return {"message": "Welcome to LingShu!"}


@app.post(
    "/channels/",
    response_model=ChannelModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Channels"],
)
async def create_channel(
    channel: ChannelModel, repo: ChannelRepository = Depends(get_channel_repository)
) -> ChannelModel:
    """创建通道.

    参数：
        channel: 要创建的通道对象.
        repo: 通道仓储实例.

    返回：
        创建后的通道对象.
    """
    if channel.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel id must be provided.",
        )
    existing_channel = repo.get_by_id(channel.id)
    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with ID '{channel.id}' already exists.",
        )
    return repo.add(channel)


@app.get("/channels/", response_model=list[ChannelModel], tags=["Channels"])
async def read_channels(repo: ChannelRepository = Depends(get_channel_repository)):
    """获取所有通道.

    参数：
        repo: 通道仓储实例.

    返回：
        所有通道对象的列表.
    """
    return repo.get_all()


@app.get("/channels/{channel_id}", response_model=ChannelModel, tags=["Channels"])
async def get_channel(channel_id: str, repo: ChannelRepository = Depends(get_channel_repository)):
    """获取通道.

    参数：
        channel_id: 要获取的通道 id.
        repo: 通道仓储实例.

    返回：
        匹配的通道对象，若不存在则为 None.
    """
    channel = repo.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
    return channel


@app.post("/channels/{channel_id}/process", tags=["Channels"])
async def process_message_for_channel(
    channel_id: str,
    message: Any = Body(..., description="Message to process"),
    repo: ChannelRepository = Depends(get_channel_repository),
):
    """处理通道消息.

    参数：
        channel_id: 要处理的通道 id.
        message: 要处理的消息.
        repo: 通道仓储实例.

    返回：
        处理后的消息.
    """
    result = await channel_processor.process_message_with_checks(channel_id, message, repo)
    return result
