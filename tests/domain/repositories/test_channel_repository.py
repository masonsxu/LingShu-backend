"""通道仓储单元测试"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.domain.models.channel import ChannelModel, HTTPDestinationConfig, HTTPSourceConfig
from app.domain.repositories.channel_repository import ChannelRepository


class TestChannelRepository:
    """通道仓储测试类"""

    @pytest.fixture
    def engine(self):
        """测试数据库引擎"""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def session(self, engine):
        """数据库会话"""
        with Session(engine) as session:
            yield session

    @pytest.fixture
    def repository(self, session):
        """仓储实例"""
        return ChannelRepository(session)

    @pytest.fixture
    def sample_channel(self):
        """示例通道"""
        return ChannelModel(
            id="test-channel-001",
            name="Test Channel",
            description="Test channel for repository testing",
            enabled=True,
            source=HTTPSourceConfig(path="/test", method="POST"),
            destinations=[HTTPDestinationConfig(url="http://test.com/webhook")],
        )

    def test_add_channel(self, repository, sample_channel):
        """测试添加通道"""
        # Act
        result = repository.add(sample_channel)

        # Assert
        assert result.id == "test-channel-001"
        assert result.name == "Test Channel"
        assert result.enabled is True

        # 验证数据库中存在
        db_channel = repository.get_by_id("test-channel-001")
        assert db_channel is not None
        assert db_channel.name == "Test Channel"

    def test_get_by_id_existing(self, repository, sample_channel):
        """测试根据ID获取存在的通道"""
        # Arrange
        repository.add(sample_channel)

        # Act
        result = repository.get_by_id("test-channel-001")

        # Assert
        assert result is not None
        assert result.id == "test-channel-001"
        assert result.name == "Test Channel"
        assert isinstance(result.source, HTTPSourceConfig)
        assert len(result.destinations) == 1

    def test_get_by_id_non_existing(self, repository):
        """测试根据ID获取不存在的通道"""
        # Act
        result = repository.get_by_id("non-existent")

        # Assert
        assert result is None

    def test_update_channel(self, repository, sample_channel):
        """测试更新通道"""
        # Arrange
        repository.add(sample_channel)

        # 修改通道
        updated_channel = sample_channel.model_copy()
        updated_channel.name = "Updated Channel Name"
        updated_channel.description = "Updated description"
        updated_channel.enabled = False

        # Act
        result = repository.update(updated_channel)

        # Assert
        assert result.name == "Updated Channel Name"
        assert result.description == "Updated description"
        assert result.enabled is False

    def test_delete_existing_channel(self, repository, sample_channel):
        """测试删除存在的通道"""
        # Arrange
        repository.add(sample_channel)

        # Act
        result = repository.delete("test-channel-001")

        # Assert
        assert result is True
        assert repository.get_by_id("test-channel-001") is None

    def test_delete_non_existing_channel(self, repository):
        """测试删除不存在的通道"""
        # Act
        result = repository.delete("non-existent")

        # Assert
        assert result is False
