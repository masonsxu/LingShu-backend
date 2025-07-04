from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, model_validator
from pydantic import Field as PydanticField
from sqlmodel import JSON, Column, Field, SQLModel


# --- 基础配置类 ---
class BaseConfig(BaseModel):
    type: str = PydanticField(
        ..., description="组件类型。"
    )  # 指定配置所属的组件类型（如 http、tcp 等）


# --- 源（Source）配置 ---
class HTTPSourceConfig(BaseConfig):
    type: Literal["http"] = "http"  # 固定为 http 类型
    path: str = PydanticField(..., description="监听的 HTTP 路径。")  # 监听的 HTTP 路径
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        ...,
        description="允许的 HTTP 方法。",  # 允许的 HTTP 方法
    )


class TCPSourceConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"  # 固定为 tcp 类型
    port: int = PydanticField(..., description="监听的 TCP 端口。")  # 监听的端口号
    host: str = PydanticField(
        "0.0.0.0", description="绑定的主机地址。"
    )  # 绑定的主机地址，默认所有网卡
    use_mllp: bool = PydanticField(
        False,
        description="是否使用 MLLP（HL7 消息）封装。",  # HL7 协议专用
    )


# 使用 Union 以支持多种 source 类型，便于扩展和序列化存储
SourceConfigType = Union[HTTPSourceConfig, TCPSourceConfig]  # 源配置类型别名


# --- 过滤器（Filter）配置 ---
class PythonScriptFilterConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"  # 固定为 python_script 类型
    script: str = PydanticField(
        ...,
        description="用于消息过滤的 Python 脚本，返回 True 保留，False 过滤。",  # 过滤逻辑脚本
    )


# 支持多种过滤器类型，便于扩展
FilterConfigType = Union[PythonScriptFilterConfig]  # 过滤器配置类型别名


# --- 转换器（Transformer）配置 ---
class PythonScriptTransformerConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"  # 固定为 python_script 类型
    script: str = PydanticField(
        ...,
        description="用于消息转换的 Python 脚本，返回转换后的消息。",  # 转换逻辑脚本
    )


# 支持多种转换器类型，便于扩展
TransformerConfigType = Union[PythonScriptTransformerConfig]  # 转换器配置类型别名


# --- 目标（Destination）配置 ---
class HTTPDestinationConfig(BaseConfig):
    type: Literal["http"] = "http"  # 固定为 http 类型
    url: str = PydanticField(..., description="目标 HTTP 地址。")  # 目标 HTTP 服务地址
    method: Literal["GET", "POST", "PUT", "DELETE"] = PydanticField(
        "POST",
        description="HTTP 请求方法。",  # 默认 POST
    )
    headers: Optional[Dict[str, str]] = PydanticField(
        None,
        description="可选的 HTTP 请求头。",  # 可选 HTTP 头
    )


class TCPDestinationConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"  # 固定为 tcp 类型
    host: str = PydanticField(..., description="目标 TCP 主机。")  # 目标主机地址
    port: int = PydanticField(..., description="目标 TCP 端口。")  # 目标端口号
    use_mllp: bool = PydanticField(
        False,
        description="是否使用 MLLP（HL7 消息）封装。",  # HL7 协议专用
    )


# 支持多种目标类型，便于扩展
DestinationConfigType = Union[
    HTTPDestinationConfig, TCPDestinationConfig
]  # 目标配置类型别名


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

    # 源配置，定义数据的输入方式（如 HTTP、TCP 等）
    source: SourceConfigType = Field(sa_column=Column(JSON), description="数据源配置。")
    # 消息过滤器列表，可选，用于消息预处理
    filters: Optional[List[FilterConfigType]] = Field(
        default=None, sa_column=Column(JSON), description="消息过滤器列表。"
    )
    # 消息转换器列表，可选，用于消息格式转换
    transformers: Optional[List[TransformerConfigType]] = Field(
        default=None, sa_column=Column(JSON), description="消息转换器列表。"
    )
    # 目标配置列表，定义消息最终流向（如 HTTP、TCP 等）
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
