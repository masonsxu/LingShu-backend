"""通道API路由器 - 符合DDD规范的实现"""
from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session

from app.api.models.channel_models import (
    ChannelCreateRequest,
    ChannelUpdateRequest, 
    ChannelResponse,
    ChannelListResponse,
    MessageProcessRequest,
    MessageProcessResponse,
    ErrorResponse
)
from app.application.services.channel_service import ChannelService
from app.application.services.channel_service_impl import ChannelServiceImpl
from app.application.channel_processor import ChannelProcessor
from app.domain.repositories.channel_repository import ChannelRepository
from app.domain.exceptions.channel_exceptions import (
    ChannelNotFoundError,
    ChannelAlreadyExistsError,
    InvalidChannelDataError,
    ChannelValidationError
)
from app.infrastructure.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])


def get_channel_repository(session: Session = Depends(get_session)) -> ChannelRepository:
    """获取通道仓储实例"""
    return ChannelRepository(session)


def get_channel_service(repo: ChannelRepository = Depends(get_channel_repository)) -> ChannelService:
    """获取通道应用服务实例"""
    return ChannelServiceImpl(repo)


def get_channel_processor() -> ChannelProcessor:
    """获取通道处理器实例"""
    return ChannelProcessor()


@router.post(
    "/",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建通道",
    description="创建一个新的数据处理通道"
)
async def create_channel(
    request: ChannelCreateRequest,
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelResponse:
    """创建通道"""
    try:
        logger.info(f"Creating channel: {request.name}")
        
        # 转换为字典（应用服务期望dict格式）
        channel_data = request.model_dump(exclude_unset=True)
        
        # 调用应用服务
        channel = await channel_service.create_channel(channel_data)
        
        # 转换为响应模型
        return ChannelResponse.from_domain(channel)
        
    except ChannelAlreadyExistsError as e:
        logger.warning(f"Channel already exists: {e.channel_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with ID '{e.channel_id}' already exists"
        )
    except (InvalidChannelDataError, ChannelValidationError) as e:
        logger.warning(f"Invalid channel data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating channel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/",
    response_model=ChannelListResponse,
    summary="获取通道列表",
    description="获取所有通道的列表"
)
async def get_channels(
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelListResponse:
    """获取所有通道"""
    try:
        logger.debug("Getting all channels")
        
        channels = await channel_service.get_all_channels()
        return ChannelListResponse.from_domain_list(channels)
        
    except Exception as e:
        logger.error(f"Error getting channels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{channel_id}",
    response_model=ChannelResponse,
    summary="获取通道详情",
    description="根据ID获取通道详情"
)
async def get_channel(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelResponse:
    """获取通道详情"""
    try:
        logger.debug(f"Getting channel: {channel_id}")
        
        channel = await channel_service.get_channel_by_id(channel_id)
        return ChannelResponse.from_domain(channel)
        
    except ChannelNotFoundError:
        logger.warning(f"Channel not found: {channel_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with ID '{channel_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{channel_id}",
    response_model=ChannelResponse,
    summary="更新通道",
    description="更新指定通道的配置"
)
async def update_channel(
    channel_id: str,
    request: ChannelUpdateRequest,
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelResponse:
    """更新通道"""
    try:
        logger.info(f"Updating channel: {channel_id}")
        
        # 转换为字典，排除未设置的字段
        update_data = request.model_dump(exclude_unset=True)
        
        # 调用应用服务
        channel = await channel_service.update_channel(channel_id, update_data)
        
        return ChannelResponse.from_domain(channel)
        
    except ChannelNotFoundError:
        logger.warning(f"Channel not found for update: {channel_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with ID '{channel_id}' not found"
        )
    except (InvalidChannelDataError, ChannelValidationError) as e:
        logger.warning(f"Invalid update data for channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除通道",
    description="删除指定的通道"
)
async def delete_channel(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
):
    """删除通道"""
    try:
        logger.info(f"Deleting channel: {channel_id}")
        
        success = await channel_service.delete_channel(channel_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete channel"
            )
            
    except ChannelNotFoundError:
        logger.warning(f"Channel not found for deletion: {channel_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with ID '{channel_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{channel_id}/process",
    response_model=MessageProcessResponse,
    summary="处理消息",
    description="通过指定通道处理消息"
)
async def process_message(
    channel_id: str,
    message: Any = Body(..., description="要处理的消息"),
    channel_service: ChannelService = Depends(get_channel_service),
    channel_processor: ChannelProcessor = Depends(get_channel_processor),
    repo: ChannelRepository = Depends(get_channel_repository)
) -> MessageProcessResponse:
    """处理消息"""
    try:
        logger.info(f"Processing message for channel: {channel_id}")
        
        # 验证通道存在且启用
        channel = await channel_service.get_channel_by_id(channel_id)
        
        # 处理消息
        result = await channel_processor.process_message_with_checks(
            channel_id, message, repo
        )
        
        # 转换为响应模型
        return MessageProcessResponse(
            process_id=result.get("process_id", "unknown"),
            status=result.get("status", "unknown"),
            message=result.get("message"),
            original_message=message,
            processed_message=result.get("processed_message"),
            destination_results=result.get("destination_results"),
            processing_time_ms=result.get("processing_time_ms")
        )
        
    except ChannelNotFoundError:
        logger.warning(f"Channel not found for message processing: {channel_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with ID '{channel_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error processing message for channel {channel_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message processing failed"
        )


# 健康检查端点
@router.get(
    "/health",
    summary="健康检查",
    description="检查通道服务健康状态"
)
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "channel-service"}