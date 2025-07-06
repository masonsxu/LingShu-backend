"""通道应用服务 - 正确的DDD实现"""
from typing import List
from abc import ABC, abstractmethod

from app.domain.models.channel import ChannelModel


class ChannelService(ABC):
    """通道应用服务接口"""
    
    @abstractmethod
    async def create_channel(self, channel_data: dict) -> ChannelModel:
        """创建通道
        
        Args:
            channel_data: 通道创建数据
            
        Returns:
            创建的通道模型
            
        Raises:
            ChannelAlreadyExistsError: 通道已存在
            InvalidChannelDataError: 无效的通道数据
        """
        pass
    
    @abstractmethod
    async def get_channel_by_id(self, channel_id: str) -> ChannelModel:
        """根据ID获取通道
        
        Args:
            channel_id: 通道ID
            
        Returns:
            通道模型
            
        Raises:
            ChannelNotFoundError: 通道不存在
        """
        pass
    
    @abstractmethod
    async def get_all_channels(self) -> List[ChannelModel]:
        """获取所有通道
        
        Returns:
            通道列表
        """
        pass
    
    @abstractmethod
    async def update_channel(self, channel_id: str, channel_data: dict) -> ChannelModel:
        """更新通道
        
        Args:
            channel_id: 通道ID
            channel_data: 更新数据
            
        Returns:
            更新后的通道模型
            
        Raises:
            ChannelNotFoundError: 通道不存在
        """
        pass
    
    @abstractmethod
    async def delete_channel(self, channel_id: str) -> bool:
        """删除通道
        
        Args:
            channel_id: 通道ID
            
        Returns:
            删除是否成功
            
        Raises:
            ChannelNotFoundError: 通道不存在
        """
        pass
    
    @abstractmethod
    async def enable_channel(self, channel_id: str) -> ChannelModel:
        """启用通道
        
        Args:
            channel_id: 通道ID
            
        Returns:
            更新后的通道模型
            
        Raises:
            ChannelNotFoundError: 通道不存在
        """
        pass
    
    @abstractmethod
    async def disable_channel(self, channel_id: str) -> ChannelModel:
        """禁用通道
        
        Args:
            channel_id: 通道ID
            
        Returns:
            更新后的通道模型
            
        Raises:
            ChannelNotFoundError: 通道不存在
        """
        pass