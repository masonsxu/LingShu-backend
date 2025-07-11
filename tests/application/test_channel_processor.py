from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, status

from app.application.channel_processor import ChannelProcessor
from app.domain.models.channel import (
    ChannelModel,
    HTTPDestinationConfig,
    HTTPSourceConfig,
)
from app.domain.repositories.channel_repository import ChannelRepository


@pytest.fixture
def mock_channel_repository():
    """Mock ChannelRepository."""
    return Mock(spec=ChannelRepository)


@pytest.fixture
def channel_processor():
    """ChannelProcessor."""
    return ChannelProcessor()


def test_create_channel_with_checks_success(mock_channel_repository, channel_processor):
    """Test create channel with checks success."""
    channel = ChannelModel(
        id="test-channel",
        name="Test Channel",
        description="Test channel for unit testing",
        enabled=True,
        source=HTTPSourceConfig(path="/test", method="POST"),
        destinations=[HTTPDestinationConfig(url="http://test", method="POST", headers={})],
    )
    mock_channel_repository.get_by_id.return_value = None
    mock_channel_repository.add.return_value = channel

    result = channel_processor.create_channel_with_checks(channel, mock_channel_repository)
    mock_channel_repository.get_by_id.assert_called_once_with("test-channel")
    mock_channel_repository.add.assert_called_once_with(channel)
    assert result == channel


def test_create_channel_with_checks_conflict(mock_channel_repository, channel_processor):
    """Test create channel with checks conflict."""
    channel = ChannelModel(
        id="test-channel",
        name="Test Channel",
        description="Test channel for unit testing",
        enabled=True,
        source=HTTPSourceConfig(path="/test", method="POST"),
        destinations=[HTTPDestinationConfig(url="http://test", method="POST", headers={})],
    )
    mock_channel_repository.get_by_id.return_value = channel

    with pytest.raises(HTTPException) as exc_info:
        channel_processor.create_channel_with_checks(channel, mock_channel_repository)
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in exc_info.value.detail
    mock_channel_repository.get_by_id.assert_called_once_with("test-channel")
    mock_channel_repository.add.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_with_checks_channel_not_found(
    mock_channel_repository, channel_processor
):
    """Test process message with checks channel not found."""
    mock_channel_repository.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await channel_processor.process_message_with_checks(
            "non-existent", "message", mock_channel_repository
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Channel not found" in exc_info.value.detail
    mock_channel_repository.get_by_id.assert_called_once_with("non-existent")


@pytest.mark.asyncio
async def test_process_message_with_checks_channel_disabled(
    mock_channel_repository, channel_processor
):
    """Test process message with checks channel disabled."""
    channel = ChannelModel(
        id="disabled-channel",
        name="Disabled Channel",
        description="Disabled channel for testing",
        enabled=False,
        source=HTTPSourceConfig(path="/test", method="POST"),
        destinations=[HTTPDestinationConfig(url="http://test", method="POST", headers={})],
    )
    mock_channel_repository.get_by_id.return_value = channel

    with pytest.raises(HTTPException) as exc_info:
        await channel_processor.process_message_with_checks(
            "disabled-channel", "message", mock_channel_repository
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Channel is disabled" in exc_info.value.detail
    mock_channel_repository.get_by_id.assert_called_once_with("disabled-channel")


@pytest.mark.asyncio
async def test_process_message_with_checks_success(mock_channel_repository, channel_processor):
    """Test process message with checks success."""
    channel = ChannelModel(
        id="enabled-channel",
        name="Enabled Channel",
        description="Enabled channel for testing",
        enabled=True,
        source=HTTPSourceConfig(path="/test", method="POST"),
        destinations=[HTTPDestinationConfig(url="http://test", method="POST", headers={})],
    )
    mock_channel_repository.get_by_id.return_value = channel

    # Mock the actual process_message to avoid complex mocking of internal logic
    channel_processor.process_message = AsyncMock(return_value={"status": "success"})

    result = await channel_processor.process_message_with_checks(
        "enabled-channel", "message", mock_channel_repository
    )
    mock_channel_repository.get_by_id.assert_called_once_with("enabled-channel")
    channel_processor.process_message.assert_called_once_with(channel, "message")
    assert result == {"status": "success"}
