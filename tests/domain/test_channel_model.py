"""通道领域模型单元测试"""

import pytest
from pydantic import ValidationError

from app.domain.models.channel import (
    ChannelModel,
    HTTPDestinationConfig,
    HTTPSourceConfig,
    PythonScriptFilterConfig,
    PythonScriptTransformerConfig,
    TCPDestinationConfig,
    TCPSourceConfig,
)


class TestChannelModel:
    """通道模型测试类"""

    @pytest.fixture
    def http_source(self):
        """HTTP源配置"""
        return HTTPSourceConfig(path="/api/messages", method="POST")

    @pytest.fixture
    def tcp_source(self):
        """TCP源配置"""
        return TCPSourceConfig(host="0.0.0.0", port=8080, use_mllp=True)

    @pytest.fixture
    def http_destination(self):
        """HTTP目标配置"""
        return HTTPDestinationConfig(url="http://localhost:8080/webhook", method="POST")

    @pytest.fixture
    def tcp_destination(self):
        """TCP目标配置"""
        return TCPDestinationConfig(host="localhost", port=8081, use_mllp=True)

    @pytest.fixture
    def python_filter(self):
        """Python过滤器配置"""
        return PythonScriptFilterConfig(script="_passed = 'test' in message.get('content', '')")

    @pytest.fixture
    def python_transformer(self):
        """Python转换器配置"""
        return PythonScriptTransformerConfig(
            script="_transformed_message = {'processed': True, 'original': message}"
        )

    def test_channel_creation_minimal(self, http_source, http_destination):
        """测试最小配置创建通道"""
        # Arrange & Act
        channel = ChannelModel(
            id="test-channel",
            name="Test Channel",
            source=http_source,
            destinations=[http_destination],
        )

        # Assert
        assert channel.id == "test-channel"
        assert channel.name == "Test Channel"
        assert channel.enabled is True  # 默认启用
        assert channel.description is None
        assert channel.filters is None
        assert channel.transformers is None
        assert len(channel.destinations) == 1
        assert isinstance(channel.source, HTTPSourceConfig)
        assert isinstance(channel.destinations[0], HTTPDestinationConfig)

    def test_channel_creation_full_config(
        self, tcp_source, http_destination, tcp_destination, python_filter, python_transformer
    ):
        """测试完整配置创建通道"""
        # Arrange & Act
        channel = ChannelModel(
            id="full-channel",
            name="Full Config Channel",
            description="Complete channel configuration",
            enabled=False,
            source=tcp_source,
            filters=[python_filter],
            transformers=[python_transformer],
            destinations=[http_destination, tcp_destination],
        )

        # Assert
        assert channel.id == "full-channel"
        assert channel.name == "Full Config Channel"
        assert channel.description == "Complete channel configuration"
        assert channel.enabled is False
        assert isinstance(channel.source, TCPSourceConfig)
        assert len(channel.filters) == 1
        assert isinstance(channel.filters[0], PythonScriptFilterConfig)
        assert len(channel.transformers) == 1
        assert isinstance(channel.transformers[0], PythonScriptTransformerConfig)
        assert len(channel.destinations) == 2
        assert isinstance(channel.destinations[0], HTTPDestinationConfig)
        assert isinstance(channel.destinations[1], TCPDestinationConfig)

    def test_channel_validation_empty_name(self, http_source, http_destination):
        """测试空名称验证"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChannelModel(
                id="test",
                name="",  # 空名称
                source=http_source,
                destinations=[http_destination],
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_channel_validation_long_name(self, http_source, http_destination):
        """测试过长名称验证"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChannelModel(
                id="test",
                name="x" * 101,  # 超过100字符
                source=http_source,
                destinations=[http_destination],
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_channel_validation_no_destinations(self, http_source):
        """测试无目标验证"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChannelModel(
                id="test",
                name="Test",
                source=http_source,
                destinations=[],  # 空目标列表
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("destinations",) for error in errors)

    def test_channel_model_dump(self, http_source, http_destination):
        """测试模型序列化"""
        # Arrange
        channel = ChannelModel(
            id="test-channel",
            name="Test Channel",
            description="Test Description",
            source=http_source,
            destinations=[http_destination],
        )

        # Act
        data = channel.model_dump()

        # Assert
        assert data["id"] == "test-channel"
        assert data["name"] == "Test Channel"
        assert data["description"] == "Test Description"
        assert data["enabled"] is True
        assert "source" in data
        assert "destinations" in data
        assert isinstance(data["source"], dict)
        assert isinstance(data["destinations"], list)

    def test_channel_json_serialization(self, http_source, http_destination):
        """测试JSON序列化"""
        # Arrange
        channel = ChannelModel(
            id="json-test",
            name="JSON Test Channel",
            source=http_source,
            destinations=[http_destination],
        )

        # Act
        json_str = channel.model_dump_json()

        # Assert
        assert '"id":"json-test"' in json_str
        assert '"name":"JSON Test Channel"' in json_str
        assert '"enabled":true' in json_str


class TestHTTPSourceConfig:
    """HTTP源配置测试"""

    def test_http_source_creation(self):
        """测试HTTP源创建"""
        # Act
        source = HTTPSourceConfig(path="/api/data", method="POST")

        # Assert
        assert source.type == "http"
        assert source.path == "/api/data"
        assert source.method == "POST"

    def test_http_source_invalid_method(self):
        """测试无效HTTP方法"""
        # Act & Assert
        with pytest.raises(ValidationError):
            HTTPSourceConfig(
                path="/api/data",
                method="INVALID",  # 无效方法
            )


class TestTCPSourceConfig:
    """TCP源配置测试"""

    def test_tcp_source_creation(self):
        """测试TCP源创建"""
        # Act
        source = TCPSourceConfig(host="192.168.1.100", port=8080, use_mllp=True)

        # Assert
        assert source.type == "tcp"
        assert source.host == "192.168.1.100"
        assert source.port == 8080
        assert source.use_mllp is True

    def test_tcp_source_defaults(self):
        """测试TCP源默认值"""
        # Act
        source = TCPSourceConfig(port=8080)

        # Assert
        assert source.host == "0.0.0.0"  # 默认值
        assert source.use_mllp is False  # 默认值


class TestDestinationConfigs:
    """目标配置测试"""

    def test_http_destination_creation(self):
        """测试HTTP目标创建"""
        # Act
        destination = HTTPDestinationConfig(
            url="https://api.example.com/webhook",
            method="PUT",
            headers={"Authorization": "Bearer token"},
        )

        # Assert
        assert destination.type == "http"
        assert destination.url == "https://api.example.com/webhook"
        assert destination.method == "PUT"
        assert destination.headers["Authorization"] == "Bearer token"

    def test_tcp_destination_creation(self):
        """测试TCP目标创建"""
        # Act
        destination = TCPDestinationConfig(host="remote.server.com", port=7777, use_mllp=True)

        # Assert
        assert destination.type == "tcp"
        assert destination.host == "remote.server.com"
        assert destination.port == 7777
        assert destination.use_mllp is True


class TestFilterConfigs:
    """过滤器配置测试"""

    def test_python_script_filter_creation(self):
        """测试Python脚本过滤器创建"""
        # Act
        filter_config = PythonScriptFilterConfig(
            script="if message.get('priority') == 'high': _passed = True"
        )

        # Assert
        assert filter_config.type == "python_script"
        assert "priority" in filter_config.script
        assert "_passed" in filter_config.script


class TestTransformerConfigs:
    """转换器配置测试"""

    def test_python_script_transformer_creation(self):
        """测试Python脚本转换器创建"""
        # Act
        transformer = PythonScriptTransformerConfig(
            script="_transformed_message = {'timestamp': datetime.now(), 'data': message}"
        )

        # Assert
        assert transformer.type == "python_script"
        assert "_transformed_message" in transformer.script
        assert "datetime.now()" in transformer.script
