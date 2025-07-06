"""通道API模型 - 请求和响应模型"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models.channel import (
    DestinationConfigType,
    FilterConfigType,
    SourceConfigType,
    TransformerConfigType,
)


class ChannelCreateRequest(BaseModel):
    """创建通道请求模型"""

    id: str | None = Field(None, description="通道ID，如果不提供将自动生成")
    name: str = Field(..., min_length=1, max_length=100, description="通道名称")
    description: str | None = Field(None, max_length=500, description="通道描述")
    enabled: bool = Field(True, description="是否启用通道")
    source: SourceConfigType = Field(..., description="数据源配置")
    filters: list[FilterConfigType] | None = Field(None, description="过滤器配置列表")
    transformers: list[TransformerConfigType] | None = Field(None, description="转换器配置列表")
    destinations: list[DestinationConfigType] = Field(..., min_items=1, description="目标配置列表")


class ChannelUpdateRequest(BaseModel):
    """更新通道请求模型"""

    name: str | None = Field(None, min_length=1, max_length=100, description="通道名称")
    description: str | None = Field(None, max_length=500, description="通道描述")
    enabled: bool | None = Field(None, description="是否启用通道")
    source: SourceConfigType | None = Field(None, description="数据源配置")
    filters: list[FilterConfigType] | None = Field(None, description="过滤器配置列表")
    transformers: list[TransformerConfigType] | None = Field(None, description="转换器配置列表")
    destinations: list[DestinationConfigType] | None = Field(
        None, min_items=1, description="目标配置列表"
    )


class ChannelResponse(BaseModel):
    """通道响应模型"""

    id: str = Field(..., description="通道ID")
    name: str = Field(..., description="通道名称")
    description: str | None = Field(None, description="通道描述")
    enabled: bool = Field(..., description="是否启用")
    source: SourceConfigType = Field(..., description="数据源配置")
    filters: list[FilterConfigType] | None = Field(None, description="过滤器配置")
    transformers: list[TransformerConfigType] | None = Field(None, description="转换器配置")
    destinations: list[DestinationConfigType] = Field(..., description="目标配置")
    created_at: datetime | None = Field(None, description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")

    @classmethod
    def from_domain(cls, channel_model) -> "ChannelResponse":
        """从领域模型创建响应模型"""
        return cls(
            id=channel_model.id,
            name=channel_model.name,
            description=channel_model.description,
            enabled=channel_model.enabled,
            source=channel_model.source,
            filters=channel_model.filters,
            transformers=channel_model.transformers,
            destinations=channel_model.destinations,
            created_at=getattr(channel_model, 'created_at', None),
            updated_at=getattr(channel_model, 'updated_at', None),
        )


class ChannelListResponse(BaseModel):
    """通道列表响应模型"""

    channels: list[ChannelResponse] = Field(..., description="通道列表")
    total: int = Field(..., description="总数量")

    @classmethod
    def from_domain_list(cls, channels: list) -> "ChannelListResponse":
        """从领域模型列表创建响应模型"""
        channel_responses = [ChannelResponse.from_domain(channel) for channel in channels]
        return cls(channels=channel_responses, total=len(channel_responses))


class MessageProcessRequest(BaseModel):
    """消息处理请求模型"""

    message: Any = Field(..., description="要处理的消息")
    content_type: str = Field("application/json", description="消息内容类型")


class MessageProcessResponse(BaseModel):
    """消息处理响应模型"""

    process_id: str = Field(..., description="处理ID")
    status: str = Field(..., description="处理状态")
    message: str | None = Field(None, description="处理消息")
    original_message: Any = Field(None, description="原始消息")
    processed_message: Any = Field(None, description="处理后消息")
    destination_results: list[dict] | None = Field(None, description="目标处理结果")
    processing_time_ms: int | None = Field(None, description="处理时间(毫秒)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="处理时间戳")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: dict | None = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间")
