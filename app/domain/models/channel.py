from typing import Literal

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import JSON, Column, Field, SQLModel


# --- 基础配置类 ---
class BaseConfig(BaseModel):
    """所有配置类的基础类型，包含类型标识."""

    type: str = PydanticField(..., description="组件类型。")


# --- 源（Source）配置 ---
class HTTPSourceConfig(BaseConfig):
    """HTTP 源配置。

    用于定义监听的 HTTP 路径和方法。
    """

    type: Literal["http"] = "http"
    path: str = PydanticField(..., description="监听的 HTTP 路径。")
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        ..., description="允许的 HTTP 方法。"
    )


class TCPSourceConfig(BaseConfig):
    """TCP 源配置。

    用于定义监听的端口、主机和是否使用 MLLP。
    """

    type: Literal["tcp"] = "tcp"
    port: int = PydanticField(..., description="监听的 TCP 端口。")
    host: str = PydanticField("0.0.0.0", description="绑定的主机地址。")
    use_mllp: bool = PydanticField(False, description="是否使用 MLLP（HL7 消息）封装。")


# 支持多种 source 类型，便于扩展和序列化存储
SourceConfigType = HTTPSourceConfig | TCPSourceConfig


# --- 过滤器（Filter）配置 ---
class PythonScriptFilterConfig(BaseConfig):
    """Python 脚本过滤器配置。

    用于自定义消息过滤逻辑。
    """

    type: Literal["python_script"] = "python_script"
    script: str = PydanticField(
        ..., description="用于消息过滤的 Python 脚本，返回 True 保留，False 过滤。"
    )


# 支持多种过滤器类型，便于扩展
FilterConfigType = PythonScriptFilterConfig


# --- 转换器（Transformer）配置 ---
class PythonScriptTransformerConfig(BaseConfig):
    """Python 脚本转换器配置。

    用于自定义消息转换逻辑。
    """

    type: Literal["python_script"] = "python_script"
    script: str = PydanticField(..., description="用于消息转换的 Python 脚本，返回转换后的消息。")


# 支持多种转换器类型，便于扩展
TransformerConfigType = PythonScriptTransformerConfig


# --- 目标（Destination）配置 ---
class HTTPDestinationConfig(BaseConfig):
    """HTTP 目标配置。

    用于定义消息发送的 HTTP 地址、方法和请求头。
    """

    type: Literal["http"] = "http"
    url: str = PydanticField(..., description="目标 HTTP 地址。")
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        "POST", description="HTTP 请求方法。"
    )
    headers: dict[str, str] | None = PydanticField(None, description="可选的 HTTP 请求头。")


class TCPDestinationConfig(BaseConfig):
    """TCP 目标配置。

    用于定义消息发送的 TCP 主机、端口和是否使用 MLLP。
    """

    type: Literal["tcp"] = "tcp"
    host: str = PydanticField(..., description="目标 TCP 主机。")
    port: int = PydanticField(..., description="目标 TCP 端口。")
    use_mllp: bool = PydanticField(False, description="是否使用 MLLP（HL7 消息）封装。")


# 支持多种目标类型，便于扩展
DestinationConfigType = HTTPDestinationConfig | TCPDestinationConfig


# --- 通道（Channel）模型 ---
class ChannelModel(SQLModel, table=True):
    """通道模型，描述数据流转的完整链路配置。

    包含源、过滤器、转换器和目标等配置，所有配置均以 JSON 形式存储，便于灵活扩展。
    """

    id: str | None = Field(default=None, primary_key=True, description="通道唯一标识。")
    name: str = Field(..., index=True, description="通道名称（便于识别）。")
    description: str | None = Field(None, description="通道描述信息。")
    enabled: bool = Field(default=True, description="通道是否启用。")

    source: SourceConfigType = Field(sa_column=Column(JSON), description="数据源配置。")
    filters: list[FilterConfigType] | None = Field(
        default=None, sa_column=Column(JSON), description="消息过滤器列表。"
    )
    transformers: list[TransformerConfigType] | None = Field(
        default=None, sa_column=Column(JSON), description="消息转换器列表。"
    )
    destinations: list[DestinationConfigType] = Field(
        sa_column=Column(JSON), description="数据目标配置列表。"
    )

    # 注意：由于SQLModel的限制，model_validator可能不会被调用
    # 我们依赖处理器中的回退逻辑来处理类型转换

    @staticmethod
    def _convert_source(source):
        if isinstance(source, dict):
            source_type = source.get("type")
            if source_type == "http":
                return HTTPSourceConfig(**source)
            if source_type == "tcp":
                return TCPSourceConfig(**source)
            # 不是已知类型，直接返回原始 source
            return HTTPSourceConfig(type="http", path="", method="GET")  # 占位，实际不会用到
        if isinstance(source, HTTPSourceConfig | TCPSourceConfig):
            return source
        # 兜底：返回一个合法的默认 HTTPSourceConfig
        return HTTPSourceConfig(type="http", path="", method="GET")

    @staticmethod
    def _convert_filters(filters):
        if not filters:
            return filters
        converted = []
        for filter_config in filters:
            if isinstance(filter_config, dict) and filter_config.get("type") == "python_script":
                converted.append(PythonScriptFilterConfig(**filter_config))
            else:
                converted.append(filter_config)
        return converted

    @staticmethod
    def _convert_transformers(transformers):
        if not transformers:
            return transformers
        converted = []
        for transformer_config in transformers:
            if (
                isinstance(transformer_config, dict)
                and transformer_config.get("type") == "python_script"
            ):
                converted.append(PythonScriptTransformerConfig(**transformer_config))
            else:
                converted.append(transformer_config)
        return converted

    @staticmethod
    def _convert_destinations(destinations):
        if not destinations:
            return destinations
        converted = []
        for destination_config in destinations:
            if isinstance(destination_config, dict):
                destination_type = destination_config.get("type")
                if destination_type == "http":
                    converted.append(HTTPDestinationConfig(**destination_config))
                elif destination_type == "tcp":
                    converted.append(TCPDestinationConfig(**destination_config))
                else:
                    converted.append(destination_config)
            else:
                converted.append(destination_config)
        return converted
