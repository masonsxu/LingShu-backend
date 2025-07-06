"""通道应用服务单元测试 - TDD示例"""
import pytest
from unittest.mock import Mock, patch
import uuid

from app.application.services.channel_service_impl import ChannelServiceImpl
from app.domain.models.channel import ChannelModel, HTTPSourceConfig, HTTPDestinationConfig
from app.domain.repositories.channel_repository import ChannelRepository
from app.domain.exceptions.channel_exceptions import (
    ChannelNotFoundError,
    ChannelAlreadyExistsError,
    InvalidChannelDataError,
    ChannelValidationError
)


class TestChannelServiceImpl:
    """通道应用服务测试类"""
    
    @pytest.fixture
    def mock_repository(self):
        """模拟仓储"""
        return Mock(spec=ChannelRepository)
    
    @pytest.fixture
    def channel_service(self, mock_repository):
        """通道服务实例"""
        return ChannelServiceImpl(mock_repository)
    
    @pytest.fixture
    def valid_channel_data(self):
        """有效的通道数据"""
        return {
            "name": "Test Channel",
            "description": "Test Description",
            "enabled": True,
            "source": {
                "type": "http",
                "path": "/test",
                "method": "POST"
            },
            "destinations": [{
                "type": "http",
                "url": "http://example.com/webhook",
                "method": "POST"
            }]
        }
    
    @pytest.fixture
    def sample_channel(self, valid_channel_data):
        """示例通道模型"""
        channel_data = {**valid_channel_data, "id": "test-channel-123"}
        return ChannelModel(**channel_data)

    # RED阶段：编写失败的测试
    @pytest.mark.asyncio
    async def test_create_channel_success(self, channel_service, mock_repository, valid_channel_data):
        """测试创建通道成功 - TDD RED阶段"""
        # Arrange
        mock_repository.get_by_id.return_value = None  # 通道不存在
        expected_channel = ChannelModel(**{**valid_channel_data, "id": "generated-id"})
        mock_repository.add.return_value = expected_channel
        
        # Act
        with patch('uuid.uuid4', return_value="generated-id"):
            result = await channel_service.create_channel(valid_channel_data)
        
        # Assert
        assert result.id == "generated-id"
        assert result.name == "Test Channel"
        mock_repository.get_by_id.assert_called_once_with("generated-id")
        mock_repository.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_channel_already_exists(self, channel_service, mock_repository, valid_channel_data, sample_channel):
        """测试创建已存在的通道 - TDD RED阶段"""
        # Arrange
        channel_data = {**valid_channel_data, "id": "existing-id"}
        mock_repository.get_by_id.return_value = sample_channel  # 通道已存在
        
        # Act & Assert
        with pytest.raises(ChannelAlreadyExistsError) as exc_info:
            await channel_service.create_channel(channel_data)
        
        assert exc_info.value.channel_id == "existing-id"
        mock_repository.get_by_id.assert_called_once_with("existing-id")
        mock_repository.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_channel_validation_error_empty_name(self, channel_service, mock_repository, valid_channel_data):
        """测试创建通道验证错误 - 空名称"""
        # Arrange
        invalid_data = {**valid_channel_data, "name": ""}
        
        # Act & Assert
        with pytest.raises(ChannelValidationError) as exc_info:
            await channel_service.create_channel(invalid_data)
        
        assert "name" in str(exc_info.value)
        mock_repository.get_by_id.assert_not_called()
        mock_repository.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_channel_validation_error_no_destinations(self, channel_service, mock_repository, valid_channel_data):
        """测试创建通道验证错误 - 无目标"""
        # Arrange
        invalid_data = {**valid_channel_data, "destinations": []}
        
        # Act & Assert
        with pytest.raises(ChannelValidationError) as exc_info:
            await channel_service.create_channel(invalid_data)
        
        assert "destinations" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_channel_by_id_success(self, channel_service, mock_repository, sample_channel):
        """测试根据ID获取通道成功"""
        # Arrange
        mock_repository.get_by_id.return_value = sample_channel
        
        # Act
        result = await channel_service.get_channel_by_id("test-channel-123")
        
        # Assert
        assert result.id == "test-channel-123"
        assert result.name == "Test Channel"
        mock_repository.get_by_id.assert_called_once_with("test-channel-123")
    
    @pytest.mark.asyncio
    async def test_get_channel_by_id_not_found(self, channel_service, mock_repository):
        """测试根据ID获取通道不存在"""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ChannelNotFoundError) as exc_info:
            await channel_service.get_channel_by_id("non-existent")
        
        assert exc_info.value.channel_id == "non-existent"
        mock_repository.get_by_id.assert_called_once_with("non-existent")
    
    @pytest.mark.asyncio
    async def test_get_channel_by_id_empty_id(self, channel_service, mock_repository):
        """测试根据空ID获取通道"""
        # Act & Assert
        with pytest.raises(InvalidChannelDataError):
            await channel_service.get_channel_by_id("")
        
        mock_repository.get_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_all_channels(self, channel_service, mock_repository, sample_channel):
        """测试获取所有通道"""
        # Arrange
        mock_repository.get_all.return_value = [sample_channel]
        
        # Act
        result = await channel_service.get_all_channels()
        
        # Assert
        assert len(result) == 1
        assert result[0].id == "test-channel-123"
        mock_repository.get_all.assert_called_once()
    
    # TDD示例：新功能 - 通道启用/禁用
    @pytest.mark.asyncio
    async def test_enable_channel_success(self, channel_service, mock_repository, sample_channel):
        """测试启用通道成功 - 新功能TDD"""
        # Arrange
        disabled_channel = sample_channel.model_copy()
        disabled_channel.enabled = False
        
        mock_repository.get_by_id.return_value = disabled_channel
        
        enabled_channel = disabled_channel.model_copy()
        enabled_channel.enabled = True
        mock_repository.update.return_value = enabled_channel
        
        # Act
        result = await channel_service.enable_channel("test-channel-123")
        
        # Assert
        assert result.enabled is True
        mock_repository.get_by_id.assert_called_once_with("test-channel-123")
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disable_channel_success(self, channel_service, mock_repository, sample_channel):
        """测试禁用通道成功 - 新功能TDD"""
        # Arrange
        mock_repository.get_by_id.return_value = sample_channel
        
        disabled_channel = sample_channel.model_copy()
        disabled_channel.enabled = False
        mock_repository.update.return_value = disabled_channel
        
        # Act
        result = await channel_service.disable_channel("test-channel-123")
        
        # Assert
        assert result.enabled is False
        mock_repository.get_by_id.assert_called_once_with("test-channel-123")
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enable_channel_not_found(self, channel_service, mock_repository):
        """测试启用不存在的通道"""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ChannelNotFoundError):
            await channel_service.enable_channel("non-existent")
        
        mock_repository.update.assert_not_called()