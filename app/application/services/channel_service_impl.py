"""通道应用服务实现 - 符合DDD规范"""

import uuid

from loguru import logger

from app.application.services.channel_service import ChannelService
from app.domain.exceptions.channel_exceptions import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
    ChannelValidationError,
    InvalidChannelDataError,
)
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository


class ChannelServiceImpl(ChannelService):
    """通道应用服务实现"""

    def __init__(self, channel_repository: ChannelRepository):
        self._channel_repository = channel_repository

    async def create_channel(self, channel_data: dict) -> ChannelModel:
        """创建通道"""
        logger.info(f"Creating channel with data: {channel_data}")

        # 1. 验证输入数据
        self._validate_channel_creation_data(channel_data)

        # 2. 生成ID（如果没有提供）
        if not channel_data.get("id"):
            channel_data["id"] = str(uuid.uuid4())

        # 3. 检查通道是否已存在
        channel_id = channel_data["id"]
        existing_channel = self._channel_repository.get_by_id(channel_id)
        if existing_channel:
            raise ChannelAlreadyExistsError(channel_id)

        # 4. 创建领域模型
        try:
            channel = ChannelModel(**channel_data)
        except Exception as e:
            raise InvalidChannelDataError(str(e))

        # 5. 持久化
        created_channel = self._channel_repository.add(channel)

        logger.info(f"Channel created successfully: {created_channel.id}")
        return created_channel

    async def get_channel_by_id(self, channel_id: str) -> ChannelModel:
        """根据ID获取通道"""
        logger.debug(f"Getting channel by ID: {channel_id}")

        if not channel_id:
            raise InvalidChannelDataError("Channel ID cannot be empty")

        channel = self._channel_repository.get_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundError(channel_id)

        return channel

    async def get_all_channels(self) -> list[ChannelModel]:
        """获取所有通道"""
        logger.debug("Getting all channels")

        channels = self._channel_repository.get_all()
        return list(channels)

    async def update_channel(self, channel_id: str, channel_data: dict) -> ChannelModel:
        """更新通道"""
        logger.info(f"Updating channel {channel_id} with data: {channel_data}")

        # 1. 验证通道存在
        existing_channel = await self.get_channel_by_id(channel_id)

        # 2. 验证更新数据
        self._validate_channel_update_data(channel_data)

        # 3. 更新数据（保持ID不变）
        update_data = {**existing_channel.model_dump(), **channel_data}
        update_data["id"] = channel_id  # 确保ID不被修改

        # 4. 创建更新后的模型
        try:
            updated_channel = ChannelModel(**update_data)
        except Exception as e:
            raise InvalidChannelDataError(str(e))

        # 5. 持久化更新
        result = self._channel_repository.update(updated_channel)

        logger.info(f"Channel updated successfully: {channel_id}")
        return result

    async def delete_channel(self, channel_id: str) -> bool:
        """删除通道"""
        logger.info(f"Deleting channel: {channel_id}")

        # 1. 验证通道存在
        await self.get_channel_by_id(channel_id)

        # 2. 执行删除
        success = self._channel_repository.delete(channel_id)

        if success:
            logger.info(f"Channel deleted successfully: {channel_id}")
        else:
            logger.warning(f"Failed to delete channel: {channel_id}")

        return success

    async def enable_channel(self, channel_id: str) -> ChannelModel:
        """启用通道"""
        logger.info(f"Enabling channel: {channel_id}")

        # 1. 获取通道
        channel = await self.get_channel_by_id(channel_id)

        # 2. 更新启用状态
        if channel.enabled:
            logger.info(f"Channel {channel_id} is already enabled")
            return channel

        # 3. 创建更新的通道
        updated_data = channel.model_dump()
        updated_data["enabled"] = True
        updated_channel = ChannelModel(**updated_data)

        # 4. 持久化
        result = self._channel_repository.update(updated_channel)

        logger.info(f"Channel enabled successfully: {channel_id}")
        return result

    async def disable_channel(self, channel_id: str) -> ChannelModel:
        """禁用通道"""
        logger.info(f"Disabling channel: {channel_id}")

        # 1. 获取通道
        channel = await self.get_channel_by_id(channel_id)

        # 2. 更新禁用状态
        if not channel.enabled:
            logger.info(f"Channel {channel_id} is already disabled")
            return channel

        # 3. 创建更新的通道
        updated_data = channel.model_dump()
        updated_data["enabled"] = False
        updated_channel = ChannelModel(**updated_data)

        # 4. 持久化
        result = self._channel_repository.update(updated_channel)

        logger.info(f"Channel disabled successfully: {channel_id}")
        return result

    def _validate_channel_creation_data(self, data: dict) -> None:
        """验证通道创建数据"""
        required_fields = ["name", "source", "destinations"]

        for field in required_fields:
            if field not in data:
                raise ChannelValidationError(field, f"Field '{field}' is required")

        # 验证名称
        name = data.get("name", "").strip()
        if not name:
            raise ChannelValidationError("name", "Name cannot be empty")

        if len(name) > 100:
            raise ChannelValidationError("name", "Name cannot exceed 100 characters")

        # 验证目标不为空
        destinations = data.get("destinations", [])
        if not destinations:
            raise ChannelValidationError("destinations", "At least one destination is required")

    def _validate_channel_update_data(self, data: dict) -> None:
        """验证通道更新数据"""
        # 更新时允许部分字段，但需要验证提供的字段
        if "name" in data:
            name = data["name"].strip()
            if not name:
                raise ChannelValidationError("name", "Name cannot be empty")
            if len(name) > 100:
                raise ChannelValidationError("name", "Name cannot exceed 100 characters")

        if "destinations" in data:
            destinations = data["destinations"]
            if not destinations:
                raise ChannelValidationError("destinations", "At least one destination is required")
