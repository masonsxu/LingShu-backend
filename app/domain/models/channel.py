from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, model_validator
from pydantic import Field as PydanticField
from sqlmodel import JSON, Column, Field, SQLModel


# --- 基础配置类 ---
class BaseConfig(BaseModel):
    """
    所有配置类的基础类型，包含类型标识。
    """

    type: str = PydanticField(..., description="组件类型。")


# --- 源（Source）配置 ---
class HTTPSourceConfig(BaseConfig):
    """
    HTTP 源配置。
    用于定义监听的 HTTP 路径和方法。
    """

    type: Literal["http"] = "http"
    path: str = PydanticField(..., description="监听的 HTTP 路径。")
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        ..., description="允许的 HTTP 方法。"
    )


class TCPSourceConfig(BaseConfig):
    """
    TCP 源配置。
    用于定义监听的端口、主机和是否使用 MLLP。
    """

    type: Literal["tcp"] = "tcp"
    port: int = PydanticField(..., description="监听的 TCP 端口。")
    host: str = PydanticField("0.0.0.0", description="绑定的主机地址。")
    use_mllp: bool = PydanticField(False, description="是否使用 MLLP（HL7 消息）封装。")


# 支持多种 source 类型，便于扩展和序列化存储
SourceConfigType = Union[HTTPSourceConfig, TCPSourceConfig]


# --- 过滤器（Filter）配置 ---
class PythonScriptFilterConfig(BaseConfig):
    """
    Python 脚本过滤器配置。
    用于自定义消息过滤逻辑。
    """

    type: Literal["python_script"] = "python_script"
    script: str = PydanticField(
        ..., description="用于消息过滤的 Python 脚本，返回 True 保留，False 过滤。"
    )


# 支持多种过滤器类型，便于扩展
FilterConfigType = Union[PythonScriptFilterConfig]


# --- 转换器（Transformer）配置 ---
class PythonScriptTransformerConfig(BaseConfig):
    """
    Python 脚本转换器配置。
    用于自定义消息转换逻辑。
    """

    type: Literal["python_script"] = "python_script"
    script: str = PydanticField(
        ..., description="用于消息转换的 Python 脚本，返回转换后的消息。"
    )


# 支持多种转换器类型，便于扩展
TransformerConfigType = Union[PythonScriptTransformerConfig]


# --- 目标（Destination）配置 ---
class HTTPDestinationConfig(BaseConfig):
    """
    HTTP 目标配置。
    用于定义消息发送的 HTTP 地址、方法和请求头。
    """

    type: Literal["http"] = "http"
    url: str = PydanticField(..., description="目标 HTTP 地址。")
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        "POST", description="HTTP 请求方法。"
    )
    headers: Optional[Dict[str, str]] = PydanticField(
        None, description="可选的 HTTP 请求头。"
    )


class TCPDestinationConfig(BaseConfig):
    """
    TCP 目标配置。
    用于定义消息发送的 TCP 主机、端口和是否使用 MLLP。
    """

    type: Literal["tcp"] = "tcp"
    host: str = PydanticField(..., description="目标 TCP 主机。")
    port: int = PydanticField(..., description="目标 TCP 端口。")
    use_mllp: bool = PydanticField(False, description="是否使用 MLLP（HL7 消息）封装。")


# 支持多种目标类型，便于扩展
DestinationConfigType = Union[HTTPDestinationConfig, TCPDestinationConfig]


# --- 通道（Channel）模型 ---
class ChannelModel(SQLModel, table=True):
    """
    通道模型，描述数据流转的完整链路配置。
    包含源、过滤器、转换器和目标等配置，所有配置均以 JSON 形式存储，便于灵活扩展。
    """

    id: Optional[str] = Field(
        default=None, primary_key=True, description="通道唯一标识。"
    )
    name: str = Field(..., index=True, description="通道名称（便于识别）。")
    description: Optional[str] = Field(None, description="通道描述信息。")
    enabled: bool = Field(default=True, description="通道是否启用。")

    source: SourceConfigType = Field(sa_column=Column(JSON), description="数据源配置。")
    filters: Optional[List[FilterConfigType]] = Field(
        default=None, sa_column=Column(JSON), description="消息过滤器列表。"
    )
    transformers: Optional[List[TransformerConfigType]] = Field(
        default=None, sa_column=Column(JSON), description="消息转换器列表。"
    )
    destinations: List[DestinationConfigType] = Field(
        sa_column=Column(JSON), description="数据目标配置列表。"
    )

    @model_validator(mode="after")
    def validate_json_fields(self) -> "ChannelModel":
        """
        反序列化时将 JSON 字典自动转换为对应的 Pydantic 配置模型，保证类型安全。
        """
        # 转换 source 字段
        if isinstance(self.source, dict):
            source_type = self.source.get("type")
            if source_type == "http":
                self.source = HTTPSourceConfig(**self.source)
            elif source_type == "tcp":
                self.source = TCPSourceConfig(**self.source)

        # 转换 filters 字段
        if self.filters:
            converted_filters = []
            for filter_config in self.filters:
                if isinstance(filter_config, dict):
                    filter_type = filter_config.get("type")
                    if filter_type == "python_script":
                        converted_filters.append(
                            PythonScriptFilterConfig(**filter_config)
                        )
                    else:
                        converted_filters.append(filter_config)
                else:
                    converted_filters.append(filter_config)
            self.filters = converted_filters

        # 转换 transformers 字段
        if self.transformers:
            converted_transformers = []
            for transformer_config in self.transformers:
                if isinstance(transformer_config, dict):
                    transformer_type = transformer_config.get("type")
                    if transformer_type == "python_script":
                        converted_transformers.append(
                            PythonScriptTransformerConfig(**transformer_config)
                        )
                    else:
                        converted_transformers.append(transformer_config)
                else:
                    converted_transformers.append(transformer_config)
            self.transformers = converted_transformers

        # 转换 destinations 字段
        if self.destinations:
            converted_destinations = []
            for destination_config in self.destinations:
                if isinstance(destination_config, dict):
                    destination_type = destination_config.get("type")
                    if destination_type == "http":
                        converted_destinations.append(
                            HTTPDestinationConfig(**destination_config)
                        )
                    elif destination_type == "tcp":
                        converted_destinations.append(
                            TCPDestinationConfig(**destination_config)
                        )
                    else:
                        converted_destinations.append(destination_config)
                else:
                    converted_destinations.append(destination_config)
            self.destinations = converted_destinations

        return self
