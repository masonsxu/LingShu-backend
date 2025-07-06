# LingShu医疗数据集成平台 - 软件详细设计文档 (SDD)

## 1. 文档概述

### 1.1 文档目的
本文档详细描述了LingShu医疗数据集成平台的软件架构设计、模块设计、接口设计、数据库设计等技术细节，为开发团队提供完整的技术实现指导。

### 1.2 文档范围
- 系统整体架构设计
- 各层次模块详细设计
- API接口设计
- 数据库设计
- 安全设计
- 部署架构设计

### 1.3 设计原则
- **领域驱动设计(DDD)**：按业务领域组织代码结构
- **测试驱动开发(TDD)**：确保代码质量和测试覆盖率
- **单一职责原则**：每个模块只负责一个功能
- **开闭原则**：对扩展开放，对修改关闭
- **依赖倒置**：依赖抽象而不是具体实现

## 2. 系统架构设计

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Presentation Layer)          │
├─────────────────────────────────────────────────────────────┤
│                         API层 (API Layer)                  │
├─────────────────────────────────────────────────────────────┤
│                       应用层 (Application Layer)           │
├─────────────────────────────────────────────────────────────┤
│                       领域层 (Domain Layer)                │
├─────────────────────────────────────────────────────────────┤
│                      基础设施层 (Infrastructure Layer)      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 DDD分层架构详解

#### 2.2.1 API层 (app/api/)
**职责**：处理HTTP请求响应，参数验证，错误处理
**主要组件**：
- **路由器 (routers.py)**：定义所有API端点
- **请求/响应模型**：Pydantic模型用于数据验证
- **异常处理器**：统一异常处理机制

#### 2.2.2 应用层 (app/application/)
**职责**：编排业务流程，协调领域对象
**主要组件**：
- **ChannelProcessor**：通道处理核心业务逻辑
- **MessageProcessor**：消息处理流程编排
- **UserService**：用户管理服务
- **MonitoringService**：监控服务

#### 2.2.3 领域层 (app/domain/)
**职责**：核心业务逻辑和规则
**主要组件**：
- **模型 (models/)**：领域实体和值对象
- **仓储接口 (repositories/)**：数据访问抽象
- **领域服务 (services/)**：跨实体的业务逻辑
- **事件 (events/)**：领域事件定义

#### 2.2.4 基础设施层 (app/infrastructure/)
**职责**：技术实现细节，外部依赖
**主要组件**：
- **数据库 (database.py)**：数据库连接和ORM配置
- **仓储实现 (repositories/)**：具体的数据访问实现
- **外部服务 (services/)**：第三方服务集成
- **配置 (config/)**：环境配置管理

## 3. 核心模块设计

### 3.1 通道管理模块

#### 3.1.1 ChannelModel (领域实体)
```python
class ChannelModel(SQLModel, table=True):
    """通道模型，描述数据流转的完整链路配置"""
    
    # 基础属性
    id: str | None = Field(primary_key=True)
    name: str = Field(index=True)
    description: str | None = Field(None)
    enabled: bool = Field(default=True)
    
    # 配置属性 (JSON存储)
    source: SourceConfigType = Field(sa_column=Column(JSON))
    filters: list[FilterConfigType] | None = Field(sa_column=Column(JSON))
    transformers: list[TransformerConfigType] | None = Field(sa_column=Column(JSON))
    destinations: list[DestinationConfigType] = Field(sa_column=Column(JSON))
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 3.1.2 配置类型系统
```python
# 源配置类型
class HTTPSourceConfig(BaseConfig):
    type: Literal["http"] = "http"
    path: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    headers: dict[str, str] | None = None

class TCPSourceConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"
    port: int
    host: str = "0.0.0.0"
    use_mllp: bool = False

SourceConfigType = HTTPSourceConfig | TCPSourceConfig

# 过滤器配置类型  
class PythonScriptFilterConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"
    script: str
    
class JSONPathFilterConfig(BaseConfig):
    type: Literal["jsonpath"] = "jsonpath"
    path: str
    condition: str

FilterConfigType = PythonScriptFilterConfig | JSONPathFilterConfig

# 转换器配置类型
class PythonScriptTransformerConfig(BaseConfig):
    type: Literal["python_script"] = "python_script"
    script: str
    
class TemplateTransformerConfig(BaseConfig):
    type: Literal["template"] = "template"
    template: str
    engine: Literal["jinja2", "mustache"] = "jinja2"

TransformerConfigType = PythonScriptTransformerConfig | TemplateTransformerConfig

# 目标配置类型
class HTTPDestinationConfig(BaseConfig):
    type: Literal["http"] = "http"
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    headers: dict[str, str] | None = None

class TCPDestinationConfig(BaseConfig):
    type: Literal["tcp"] = "tcp"
    host: str
    port: int
    use_mllp: bool = False

DestinationConfigType = HTTPDestinationConfig | TCPDestinationConfig
```

#### 3.1.3 ChannelRepository (仓储接口)
```python
from abc import ABC, abstractmethod
from collections.abc import Sequence

class ChannelRepository(ABC):
    """通道仓储接口"""
    
    @abstractmethod
    def get_by_id(self, channel_id: str) -> ChannelModel | None:
        """根据ID获取通道"""
        pass
    
    @abstractmethod
    def get_all(self) -> Sequence[ChannelModel]:
        """获取所有通道"""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> ChannelModel | None:
        """根据名称获取通道"""
        pass
    
    @abstractmethod
    def add(self, channel: ChannelModel) -> ChannelModel:
        """添加通道"""
        pass
    
    @abstractmethod
    def update(self, channel: ChannelModel) -> ChannelModel:
        """更新通道"""
        pass
    
    @abstractmethod
    def delete(self, channel_id: str) -> bool:
        """删除通道"""
        pass
    
    @abstractmethod
    def get_enabled_channels(self) -> Sequence[ChannelModel]:
        """获取启用的通道"""
        pass
```

#### 3.1.4 ChannelProcessor (应用服务)
```python
class ChannelProcessor:
    """通道处理器：负责通道的创建校验、消息处理等核心业务逻辑"""
    
    def __init__(self, 
                 channel_repo: ChannelRepository,
                 message_processor: MessageProcessor,
                 logger: Logger):
        self.channel_repo = channel_repo
        self.message_processor = message_processor
        self.logger = logger
    
    def create_channel_with_checks(self, channel: ChannelModel) -> ChannelModel:
        """创建通道前进行唯一性和参数校验"""
        # 业务规则验证
        self._validate_channel_business_rules(channel)
        # 唯一性检查
        self._check_channel_uniqueness(channel)
        # 创建通道
        return self.channel_repo.add(channel)
    
    def update_channel_with_checks(self, channel: ChannelModel) -> ChannelModel:
        """更新通道前进行校验"""
        # 存在性检查
        existing = self.channel_repo.get_by_id(channel.id)
        if not existing:
            raise ChannelNotFoundError(f"Channel {channel.id} not found")
        # 业务规则验证
        self._validate_channel_business_rules(channel)
        # 更新通道
        return self.channel_repo.update(channel)
    
    async def process_message_with_checks(self, 
                                        channel_id: str, 
                                        message: Any) -> MessageProcessResult:
        """校验通道状态后处理消息"""
        channel = self.channel_repo.get_by_id(channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        if not channel.enabled:
            raise ChannelDisabledError(f"Channel {channel_id} is disabled")
        
        return await self.message_processor.process_message(channel, message)
    
    def _validate_channel_business_rules(self, channel: ChannelModel):
        """验证通道业务规则"""
        # 至少有一个目标
        if not channel.destinations:
            raise InvalidChannelConfigError("Channel must have at least one destination")
        
        # 验证源配置
        self._validate_source_config(channel.source)
        
        # 验证过滤器配置
        if channel.filters:
            for filter_config in channel.filters:
                self._validate_filter_config(filter_config)
        
        # 验证转换器配置
        if channel.transformers:
            for transformer_config in channel.transformers:
                self._validate_transformer_config(transformer_config)
        
        # 验证目标配置
        for destination_config in channel.destinations:
            self._validate_destination_config(destination_config)
    
    def _check_channel_uniqueness(self, channel: ChannelModel):
        """检查通道唯一性"""
        if channel.id:
            existing = self.channel_repo.get_by_id(channel.id)
            if existing:
                raise ChannelAlreadyExistsError(f"Channel {channel.id} already exists")
        
        existing_by_name = self.channel_repo.get_by_name(channel.name)
        if existing_by_name and existing_by_name.id != channel.id:
            raise ChannelNameConflictError(f"Channel name '{channel.name}' already exists")
```

### 3.2 消息处理模块

#### 3.2.1 MessageProcessor (应用服务)
```python
class MessageProcessor:
    """消息处理器：负责消息的过滤、转换、分发等处理流程"""
    
    def __init__(self, 
                 filter_engine: FilterEngine,
                 transformer_engine: TransformerEngine,
                 dispatcher: MessageDispatcher,
                 logger: Logger):
        self.filter_engine = filter_engine
        self.transformer_engine = transformer_engine
        self.dispatcher = dispatcher
        self.logger = logger
    
    async def process_message(self, 
                            channel: ChannelModel, 
                            message: Any) -> MessageProcessResult:
        """按通道配置依次执行过滤、转换、分发等处理流程"""
        
        process_id = self._generate_process_id()
        self.logger.info(f"Processing message for channel '{channel.name}' (ID: {channel.id})")
        
        try:
            # 1. 过滤阶段
            filter_result = await self._apply_filters(channel, message, process_id)
            if filter_result.filtered:
                return MessageProcessResult(
                    process_id=process_id,
                    status=ProcessStatus.FILTERED,
                    message=filter_result.reason,
                    original_message=message
                )
            
            current_message = filter_result.message
            
            # 2. 转换阶段
            transform_result = await self._apply_transformers(channel, current_message, process_id)
            if transform_result.error:
                return MessageProcessResult(
                    process_id=process_id,
                    status=ProcessStatus.TRANSFORM_ERROR,
                    message=transform_result.error,
                    original_message=message
                )
            
            transformed_message = transform_result.message
            
            # 3. 分发阶段
            dispatch_results = await self._dispatch_to_destinations(
                channel, transformed_message, process_id
            )
            
            # 4. 生成处理结果
            return MessageProcessResult(
                process_id=process_id,
                status=ProcessStatus.SUCCESS,
                original_message=message,
                processed_message=transformed_message,
                destination_results=dispatch_results
            )
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing message: {e}")
            return MessageProcessResult(
                process_id=process_id,
                status=ProcessStatus.ERROR,
                message=str(e),
                original_message=message
            )
    
    async def _apply_filters(self, 
                           channel: ChannelModel, 
                           message: Any, 
                           process_id: str) -> FilterResult:
        """应用过滤器"""
        if not channel.filters:
            return FilterResult(filtered=False, message=message)
        
        for i, filter_config in enumerate(channel.filters):
            result = await self.filter_engine.apply_filter(filter_config, message)
            if result.filtered:
                self.logger.info(f"Message filtered by filter {i}: {result.reason}")
                return result
            message = result.message
        
        return FilterResult(filtered=False, message=message)
    
    async def _apply_transformers(self, 
                                channel: ChannelModel, 
                                message: Any, 
                                process_id: str) -> TransformResult:
        """应用转换器"""
        if not channel.transformers:
            return TransformResult(message=message)
        
        for i, transformer_config in enumerate(channel.transformers):
            result = await self.transformer_engine.apply_transformer(transformer_config, message)
            if result.error:
                self.logger.error(f"Transform error at transformer {i}: {result.error}")
                return result
            message = result.message
        
        return TransformResult(message=message)
    
    async def _dispatch_to_destinations(self, 
                                      channel: ChannelModel, 
                                      message: Any, 
                                      process_id: str) -> list[DispatchResult]:
        """分发到目标"""
        dispatch_tasks = []
        for destination_config in channel.destinations:
            task = self.dispatcher.dispatch_message(destination_config, message)
            dispatch_tasks.append(task)
        
        results = await asyncio.gather(*dispatch_tasks, return_exceptions=True)
        
        dispatch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                dispatch_results.append(DispatchResult(
                    destination_index=i,
                    success=False,
                    error=str(result)
                ))
            else:
                dispatch_results.append(result)
        
        return dispatch_results
```

#### 3.2.2 过滤引擎设计
```python
class FilterEngine:
    """过滤引擎：负责执行各种类型的过滤器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.filter_handlers = {
            "python_script": self._handle_python_script_filter,
            "jsonpath": self._handle_jsonpath_filter,
            "regex": self._handle_regex_filter,
        }
    
    async def apply_filter(self, filter_config: FilterConfigType, message: Any) -> FilterResult:
        """应用过滤器"""
        handler = self.filter_handlers.get(filter_config.type)
        if not handler:
            raise UnsupportedFilterTypeError(f"Unsupported filter type: {filter_config.type}")
        
        return await handler(filter_config, message)
    
    async def _handle_python_script_filter(self, 
                                         filter_config: PythonScriptFilterConfig, 
                                         message: Any) -> FilterResult:
        """处理Python脚本过滤器"""
        try:
            local_vars = {
                "message": message,
                "_passed": False,
                "_modified_message": None
            }
            
            # 执行脚本
            exec(filter_config.script, {}, local_vars)
            
            # 检查过滤结果
            if not local_vars.get("_passed", False):
                return FilterResult(
                    filtered=True,
                    reason="Message filtered by Python script"
                )
            
            # 返回可能修改的消息
            modified_message = local_vars.get("_modified_message")
            return FilterResult(
                filtered=False,
                message=modified_message if modified_message is not None else message
            )
            
        except Exception as e:
            self.logger.error(f"Error executing Python script filter: {e}")
            return FilterResult(
                filtered=True,
                reason=f"Filter script error: {e}"
            )
    
    async def _handle_jsonpath_filter(self, 
                                    filter_config: JSONPathFilterConfig, 
                                    message: Any) -> FilterResult:
        """处理JSONPath过滤器"""
        try:
            from jsonpath_ng import parse
            
            # 解析JSONPath表达式
            jsonpath_expr = parse(filter_config.path)
            matches = jsonpath_expr.find(message)
            
            if not matches:
                return FilterResult(
                    filtered=True,
                    reason=f"JSONPath '{filter_config.path}' not found"
                )
            
            # 检查条件
            value = matches[0].value
            if not self._evaluate_condition(value, filter_config.condition):
                return FilterResult(
                    filtered=True,
                    reason=f"JSONPath condition '{filter_config.condition}' not met"
                )
            
            return FilterResult(filtered=False, message=message)
            
        except Exception as e:
            self.logger.error(f"Error executing JSONPath filter: {e}")
            return FilterResult(
                filtered=True,
                reason=f"JSONPath filter error: {e}"
            )
```

#### 3.2.3 转换引擎设计
```python
class TransformerEngine:
    """转换引擎：负责执行各种类型的转换器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.transformer_handlers = {
            "python_script": self._handle_python_script_transformer,
            "template": self._handle_template_transformer,
            "hl7_to_fhir": self._handle_hl7_to_fhir_transformer,
            "fhir_to_hl7": self._handle_fhir_to_hl7_transformer,
        }
    
    async def apply_transformer(self, 
                              transformer_config: TransformerConfigType, 
                              message: Any) -> TransformResult:
        """应用转换器"""
        handler = self.transformer_handlers.get(transformer_config.type)
        if not handler:
            raise UnsupportedTransformerTypeError(
                f"Unsupported transformer type: {transformer_config.type}"
            )
        
        return await handler(transformer_config, message)
    
    async def _handle_python_script_transformer(self, 
                                              transformer_config: PythonScriptTransformerConfig, 
                                              message: Any) -> TransformResult:
        """处理Python脚本转换器"""
        try:
            local_vars = {
                "message": message,
                "_transformed_message": None,
            }
            
            # 执行脚本
            exec(transformer_config.script, {}, local_vars)
            
            # 获取转换结果
            transformed_message = local_vars.get("_transformed_message")
            if transformed_message is None:
                self.logger.warning("Transformer script did not set '_transformed_message'")
                return TransformResult(message=message)
            
            return TransformResult(message=transformed_message)
            
        except Exception as e:
            self.logger.error(f"Error executing Python script transformer: {e}")
            return TransformResult(
                message=message,
                error=f"Transformer script error: {e}"
            )
    
    async def _handle_template_transformer(self, 
                                         transformer_config: TemplateTransformerConfig, 
                                         message: Any) -> TransformResult:
        """处理模板转换器"""
        try:
            if transformer_config.engine == "jinja2":
                from jinja2 import Template
                template = Template(transformer_config.template)
                result = template.render(message=message)
            else:
                raise UnsupportedTemplateEngineError(
                    f"Unsupported template engine: {transformer_config.engine}"
                )
            
            return TransformResult(message=result)
            
        except Exception as e:
            self.logger.error(f"Error executing template transformer: {e}")
            return TransformResult(
                message=message,
                error=f"Template transformer error: {e}"
            )
```

### 3.3 消息分发模块

#### 3.3.1 MessageDispatcher (应用服务)
```python
class MessageDispatcher:
    """消息分发器：负责将消息发送到各种目标"""
    
    def __init__(self, 
                 http_client: HTTPClient,
                 tcp_client: TCPClient,
                 logger: Logger):
        self.http_client = http_client
        self.tcp_client = tcp_client
        self.logger = logger
        self.dispatch_handlers = {
            "http": self._dispatch_to_http,
            "tcp": self._dispatch_to_tcp,
            "file": self._dispatch_to_file,
            "database": self._dispatch_to_database,
        }
    
    async def dispatch_message(self, 
                             destination_config: DestinationConfigType, 
                             message: Any) -> DispatchResult:
        """分发消息到目标"""
        handler = self.dispatch_handlers.get(destination_config.type)
        if not handler:
            raise UnsupportedDestinationTypeError(
                f"Unsupported destination type: {destination_config.type}"
            )
        
        return await handler(destination_config, message)
    
    async def _dispatch_to_http(self, 
                              destination_config: HTTPDestinationConfig, 
                              message: Any) -> DispatchResult:
        """分发到HTTP目标"""
        try:
            response = await self.http_client.send_request(
                method=destination_config.method,
                url=destination_config.url,
                headers=destination_config.headers,
                data=message
            )
            
            return DispatchResult(
                destination_type="http",
                success=True,
                response_code=response.status_code,
                response_body=response.text
            )
            
        except Exception as e:
            self.logger.error(f"Error dispatching to HTTP destination: {e}")
            return DispatchResult(
                destination_type="http",
                success=False,
                error=str(e)
            )
    
    async def _dispatch_to_tcp(self, 
                             destination_config: TCPDestinationConfig, 
                             message: Any) -> DispatchResult:
        """分发到TCP目标"""
        try:
            result = await self.tcp_client.send_message(
                host=destination_config.host,
                port=destination_config.port,
                message=message,
                use_mllp=destination_config.use_mllp
            )
            
            return DispatchResult(
                destination_type="tcp",
                success=True,
                bytes_sent=result.bytes_sent
            )
            
        except Exception as e:
            self.logger.error(f"Error dispatching to TCP destination: {e}")
            return DispatchResult(
                destination_type="tcp",
                success=False,
                error=str(e)
            )
```

## 4. API接口设计

### 4.1 RESTful API设计

#### 4.1.1 通道管理API
```python
# 通道CRUD操作
GET    /api/v1/channels              # 获取通道列表
POST   /api/v1/channels              # 创建通道
GET    /api/v1/channels/{id}         # 获取通道详情
PUT    /api/v1/channels/{id}         # 更新通道
DELETE /api/v1/channels/{id}         # 删除通道

# 通道状态管理
PUT    /api/v1/channels/{id}/enable  # 启用通道
PUT    /api/v1/channels/{id}/disable # 禁用通道

# 通道配置管理
GET    /api/v1/channels/{id}/config  # 获取通道配置
PUT    /api/v1/channels/{id}/config  # 更新通道配置
POST   /api/v1/channels/{id}/validate # 验证通道配置
```

#### 4.1.2 消息处理API
```python
# 消息处理
POST   /api/v1/channels/{id}/messages # 发送消息到通道
GET    /api/v1/channels/{id}/messages # 获取通道消息历史

# 消息处理状态
GET    /api/v1/messages/{process_id}  # 获取消息处理状态
```

#### 4.1.3 监控API
```python
# 通道监控
GET    /api/v1/channels/{id}/stats    # 获取通道统计信息
GET    /api/v1/channels/{id}/health   # 获取通道健康状态

# 系统监控
GET    /api/v1/system/health          # 系统健康检查
GET    /api/v1/system/metrics         # 系统指标
```

### 4.2 请求/响应模型

#### 4.2.1 通道相关模型
```python
class ChannelCreateRequest(BaseModel):
    """创建通道请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    enabled: bool = Field(default=True)
    source: SourceConfigType
    filters: list[FilterConfigType] | None = None
    transformers: list[TransformerConfigType] | None = None
    destinations: list[DestinationConfigType]

class ChannelUpdateRequest(BaseModel):
    """更新通道请求"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    enabled: bool | None = None
    source: SourceConfigType | None = None
    filters: list[FilterConfigType] | None = None
    transformers: list[TransformerConfigType] | None = None
    destinations: list[DestinationConfigType] | None = None

class ChannelResponse(BaseModel):
    """通道响应"""
    id: str
    name: str
    description: str | None
    enabled: bool
    source: SourceConfigType
    filters: list[FilterConfigType] | None
    transformers: list[TransformerConfigType] | None
    destinations: list[DestinationConfigType]
    created_at: datetime
    updated_at: datetime

class ChannelListResponse(BaseModel):
    """通道列表响应"""
    channels: list[ChannelResponse]
    total: int
    page: int
    page_size: int
```

#### 4.2.2 消息处理模型
```python
class MessageProcessRequest(BaseModel):
    """消息处理请求"""
    message: Any
    content_type: str = Field(default="application/json")
    
class MessageProcessResponse(BaseModel):
    """消息处理响应"""
    process_id: str
    status: ProcessStatus
    original_message: Any
    processed_message: Any | None = None
    destination_results: list[DispatchResult]
    processing_time_ms: int
    timestamp: datetime
```

## 5. 数据库设计

### 5.1 数据库表结构

#### 5.1.1 通道表 (channels)
```sql
CREATE TABLE channels (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    source JSON NOT NULL,
    filters JSON,
    transformers JSON,
    destinations JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_enabled (enabled)
);
```

#### 5.1.2 消息处理日志表 (message_logs)
```sql
CREATE TABLE message_logs (
    id VARCHAR(50) PRIMARY KEY,
    channel_id VARCHAR(50) NOT NULL,
    process_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    original_message TEXT,
    processed_message TEXT,
    error_message TEXT,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id),
    INDEX idx_channel_id (channel_id),
    INDEX idx_process_id (process_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

#### 5.1.3 用户表 (users)
```sql
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    enabled BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
);
```

### 5.2 数据库迁移策略

#### 5.2.1 迁移脚本管理
```python
# migrations/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """创建初始表结构"""
    op.create_table(
        'channels',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('source', sa.JSON, nullable=False),
        sa.Column('filters', sa.JSON),
        sa.Column('transformers', sa.JSON),
        sa.Column('destinations', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.current_timestamp()),
    )
    
    op.create_index('idx_channels_name', 'channels', ['name'])
    op.create_index('idx_channels_enabled', 'channels', ['enabled'])

def downgrade():
    """回滚迁移"""
    op.drop_table('channels')
```

## 6. 安全设计

### 6.1 认证和授权

#### 6.1.1 JWT认证
```python
class AuthService:
    """认证服务"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, user_id: str, expires_delta: timedelta = None) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode = {"sub": user_id, "exp": expire}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> str:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise InvalidTokenError("Invalid token")
            return user_id
        except PyJWTError:
            raise InvalidTokenError("Invalid token")
```

#### 6.1.2 基于角色的访问控制 (RBAC)
```python
class Permission(str, Enum):
    """权限枚举"""
    READ_CHANNEL = "read_channel"
    WRITE_CHANNEL = "write_channel"
    DELETE_CHANNEL = "delete_channel"
    ADMIN = "admin"

class Role(str, Enum):
    """角色枚举"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ_CHANNEL, Permission.WRITE_CHANNEL, Permission.DELETE_CHANNEL, Permission.ADMIN],
    Role.OPERATOR: [Permission.READ_CHANNEL, Permission.WRITE_CHANNEL],
    Role.VIEWER: [Permission.READ_CHANNEL],
}

def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中获取用户信息
            user = get_current_user()
            if not has_permission(user, permission):
                raise PermissionDeniedError(f"Permission {permission} required")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 6.2 数据安全

#### 6.2.1 数据加密
```python
class EncryptionService:
    """数据加密服务"""
    
    def __init__(self, key: bytes):
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_sensitive_config(self, config: dict) -> dict:
        """加密敏感配置"""
        sensitive_fields = ['password', 'secret', 'token', 'key']
        encrypted_config = config.copy()
        
        for field in sensitive_fields:
            if field in encrypted_config:
                encrypted_config[field] = self.encrypt(encrypted_config[field])
        
        return encrypted_config
```

#### 6.2.2 审计日志
```python
class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def log_action(self, 
                   user_id: str, 
                   action: str, 
                   resource_type: str, 
                   resource_id: str, 
                   details: dict = None):
        """记录用户操作"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        }
        
        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")
```

## 7. 性能优化设计

### 7.1 缓存策略

#### 7.1.1 多级缓存架构
```python
class CacheService:
    """缓存服务"""
    
    def __init__(self, 
                 redis_client: Redis,
                 local_cache: Dict[str, Any],
                 default_ttl: int = 300):
        self.redis = redis_client
        self.local_cache = local_cache
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Any:
        """获取缓存数据"""
        # 1. 先查本地缓存
        if key in self.local_cache:
            return self.local_cache[key]
        
        # 2. 查Redis缓存
        value = await self.redis.get(key)
        if value:
            # 同步到本地缓存
            self.local_cache[key] = json.loads(value)
            return self.local_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存数据"""
        ttl = ttl or self.default_ttl
        
        # 设置本地缓存
        self.local_cache[key] = value
        
        # 设置Redis缓存
        await self.redis.setex(key, ttl, json.dumps(value))
```

### 7.2 异步处理

#### 7.2.1 消息队列处理
```python
class MessageQueue:
    """消息队列处理器"""
    
    def __init__(self, queue_url: str):
        self.queue_url = queue_url
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """连接消息队列"""
        self.connection = await aio_pika.connect_robust(self.queue_url)
        self.channel = await self.connection.channel()
    
    async def publish_message(self, 
                            routing_key: str, 
                            message: dict, 
                            priority: int = 0):
        """发布消息到队列"""
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                json.dumps(message).encode(),
                priority=priority,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
    
    async def consume_messages(self, 
                             queue_name: str, 
                             callback: Callable):
        """消费队列消息"""
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.consume(callback)
```

## 8. 测试策略

### 8.1 测试金字塔

#### 8.1.1 单元测试（70%）
```python
# tests/domain/test_channel_model.py
class TestChannelModel:
    """通道模型单元测试"""
    
    def test_channel_creation_with_valid_data(self):
        """测试使用有效数据创建通道"""
        channel = ChannelModel(
            id="test-channel",
            name="Test Channel",
            source=HTTPSourceConfig(path="/test", method="POST"),
            destinations=[HTTPDestinationConfig(url="http://example.com")]
        )
        
        assert channel.id == "test-channel"
        assert channel.name == "Test Channel"
        assert channel.enabled is True
        assert isinstance(channel.source, HTTPSourceConfig)
    
    def test_channel_validation_fails_with_invalid_source(self):
        """测试无效源配置时验证失败"""
        with pytest.raises(ValidationError):
            ChannelModel(
                id="test-channel",
                name="Test Channel",
                source={"invalid": "config"},
                destinations=[HTTPDestinationConfig(url="http://example.com")]
            )
```

#### 8.1.2 集成测试（20%）
```python
# tests/integration/test_channel_api.py
class TestChannelAPI:
    """通道API集成测试"""
    
    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        async with AsyncSession(test_engine) as session:
            # 创建测试表
            await session.execute(text("CREATE TABLE IF NOT EXISTS channels (...)"))
            await session.commit()
    
    async def test_create_channel_success(self, client: AsyncClient):
        """测试创建通道成功"""
        channel_data = {
            "id": "test-channel",
            "name": "Test Channel",
            "source": {
                "type": "http",
                "path": "/test",
                "method": "POST"
            },
            "destinations": [{
                "type": "http",
                "url": "http://example.com"
            }]
        }
        
        response = await client.post("/api/v1/channels", json=channel_data)
        
        assert response.status_code == 201
        assert response.json()["id"] == "test-channel"
        assert response.json()["name"] == "Test Channel"
```

#### 8.1.3 端到端测试（10%）
```python
# tests/e2e/test_message_processing.py
class TestMessageProcessingE2E:
    """消息处理端到端测试"""
    
    async def test_complete_message_processing_flow(self, client: AsyncClient):
        """测试完整的消息处理流程"""
        # 1. 创建通道
        channel_data = {
            "id": "e2e-channel",
            "name": "E2E Test Channel",
            "source": {
                "type": "http",
                "path": "/e2e-test",
                "method": "POST"
            },
            "filters": [{
                "type": "python_script",
                "script": "_passed = 'test' in message.get('content', '')"
            }],
            "transformers": [{
                "type": "python_script",
                "script": "_transformed_message = {'transformed': True, 'original': message}"
            }],
            "destinations": [{
                "type": "http",
                "url": "http://mock-destination.com/webhook"
            }]
        }
        
        create_response = await client.post("/api/v1/channels", json=channel_data)
        assert create_response.status_code == 201
        
        # 2. 发送消息
        message_data = {
            "message": {"content": "test message", "timestamp": "2024-01-01T00:00:00Z"}
        }
        
        process_response = await client.post(
            "/api/v1/channels/e2e-channel/messages",
            json=message_data
        )
        
        assert process_response.status_code == 200
        result = process_response.json()
        assert result["status"] == "success"
        assert result["processed_message"]["transformed"] is True
```

### 8.2 测试数据管理

#### 8.2.1 测试夹具
```python
# tests/fixtures/channel_fixtures.py
@pytest.fixture
def sample_http_source():
    """示例HTTP源配置"""
    return HTTPSourceConfig(
        path="/api/messages",
        method="POST"
    )

@pytest.fixture
def sample_http_destination():
    """示例HTTP目标配置"""
    return HTTPDestinationConfig(
        url="http://localhost:8080/webhook",
        method="POST",
        headers={"Content-Type": "application/json"}
    )

@pytest.fixture
def sample_channel(sample_http_source, sample_http_destination):
    """示例通道"""
    return ChannelModel(
        id="test-channel-001",
        name="Test Channel",
        description="Test channel for unit testing",
        source=sample_http_source,
        destinations=[sample_http_destination]
    )
```

### 8.3 性能测试

#### 8.3.1 负载测试
```python
# tests/performance/test_channel_performance.py
class TestChannelPerformance:
    """通道性能测试"""
    
    async def test_channel_creation_performance(self, client: AsyncClient):
        """测试通道创建性能"""
        start_time = time.time()
        
        # 创建1000个通道
        tasks = []
        for i in range(1000):
            channel_data = {
                "id": f"perf-channel-{i}",
                "name": f"Performance Test Channel {i}",
                "source": {
                    "type": "http",
                    "path": f"/perf-test-{i}",
                    "method": "POST"
                },
                "destinations": [{
                    "type": "http",
                    "url": f"http://example.com/webhook-{i}"
                }]
            }
            tasks.append(client.post("/api/v1/channels", json=channel_data))
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        assert all(r.status_code == 201 for r in responses)
        assert end_time - start_time < 10.0  # 应在10秒内完成
    
    async def test_message_processing_throughput(self, client: AsyncClient):
        """测试消息处理吞吐量"""
        # 创建测试通道
        channel_data = {
            "id": "throughput-channel",
            "name": "Throughput Test Channel",
            "source": {
                "type": "http",
                "path": "/throughput-test",
                "method": "POST"
            },
            "destinations": [{
                "type": "http",
                "url": "http://mock-destination.com/webhook"
            }]
        }
        
        await client.post("/api/v1/channels", json=channel_data)
        
        # 并发发送消息
        start_time = time.time()
        
        tasks = []
        for i in range(1000):
            message_data = {
                "message": {"id": i, "content": f"test message {i}"}
            }
            tasks.append(
                client.post(
                    "/api/v1/channels/throughput-channel/messages",
                    json=message_data
                )
            )
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        success_count = sum(1 for r in responses if r.status_code == 200)
        throughput = success_count / (end_time - start_time)
        
        assert success_count >= 950  # 95%成功率
        assert throughput >= 100     # 每秒至少100条消息
```

## 9. 部署架构设计

### 9.1 Docker容器化

#### 9.1.1 Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 9.1.2 Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/lingshu
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=lingshu
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 9.2 Kubernetes部署

#### 9.2.1 部署配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lingshu-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lingshu-api
  template:
    metadata:
      labels:
        app: lingshu-api
    spec:
      containers:
      - name: api
        image: lingshu/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lingshu-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: lingshu-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

## 10. 监控和日志

### 10.1 应用监控

#### 10.1.1 Prometheus指标
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
message_processed_total = Counter(
    'lingshu_messages_processed_total',
    'Total number of messages processed',
    ['channel_id', 'status']
)

message_processing_duration = Histogram(
    'lingshu_message_processing_duration_seconds',
    'Time spent processing messages',
    ['channel_id']
)

active_channels = Gauge(
    'lingshu_active_channels',
    'Number of active channels'
)

class MonitoringMiddleware:
    """监控中间件"""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 记录指标
        duration = time.time() - start_time
        
        # 记录API调用指标
        api_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        api_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
```

### 10.2 结构化日志

#### 10.2.1 日志配置
```python
import structlog

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class LoggerService:
    """日志服务"""
    
    def __init__(self):
        self.logger = structlog.get_logger()
    
    def log_message_processing(self, 
                             channel_id: str, 
                             process_id: str, 
                             status: str, 
                             duration_ms: int):
        """记录消息处理日志"""
        self.logger.info(
            "Message processed",
            channel_id=channel_id,
            process_id=process_id,
            status=status,
            duration_ms=duration_ms
        )
    
    def log_error(self, 
                  error: Exception, 
                  context: dict = None):
        """记录错误日志"""
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {}
        )
```

## 11. 开发和部署流程

### 11.1 CI/CD流程

#### 11.1.1 GitHub Actions配置
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Run linting
      run: |
        ruff check app/
        ruff format --check app/
    
    - name: Run type checking
      run: |
        mypy app/

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to DockerHub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: lingshu/api:latest
        
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # 部署到生产环境的脚本
        echo "Deploying to production..."
```

### 11.2 环境配置

#### 11.2.1 环境变量配置
```python
# app/config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    database_url: str = "sqlite:///./lingshu.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 安全配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    
    # 性能配置
    max_concurrent_messages: int = 1000
    message_timeout_seconds: int = 300
    
    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 获取配置实例
settings = Settings()
```

## 12. 文档和维护

### 12.1 API文档

#### 12.1.1 OpenAPI规范
```python
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="LingShu Medical Data Integration Platform",
    description="A modern platform for healthcare data integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

def custom_openapi():
    """自定义OpenAPI规范"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="LingShu API",
        version="1.0.0",
        description="LingShu医疗数据集成平台API文档",
        routes=app.routes,
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 12.2 代码文档

#### 12.2.1 文档字符串规范
```python
def create_channel_with_checks(self, channel: ChannelModel) -> ChannelModel:
    """创建通道前进行唯一性和参数校验。

    Args:
        channel: 待创建的通道对象，包含完整的配置信息

    Returns:
        ChannelModel: 创建成功的通道对象，包含生成的ID和时间戳

    Raises:
        InvalidChannelConfigError: 当通道配置不符合业务规则时抛出
        ChannelAlreadyExistsError: 当通道ID或名称已存在时抛出
        DatabaseError: 当数据库操作失败时抛出

    Examples:
        >>> channel = ChannelModel(
        ...     name="Test Channel",
        ...     source=HTTPSourceConfig(path="/test", method="POST"),
        ...     destinations=[HTTPDestinationConfig(url="http://example.com")]
        ... )
        >>> created_channel = processor.create_channel_with_checks(channel)
        >>> print(created_channel.id)
        'generated-uuid-here'
    """
```

## 13. 总结

本软件详细设计文档基于DDD和TDD原则，为LingShu医疗数据集成平台提供了完整的技术实现指导。文档涵盖了从架构设计到部署运维的各个方面，确保系统的可扩展性、可维护性和可靠性。

### 13.1 设计亮点

1. **清晰的分层架构**：严格按照DDD原则组织代码结构
2. **完善的类型系统**：利用Python类型提示和Pydantic验证
3. **全面的测试策略**：单元测试、集成测试、端到端测试
4. **现代化的技术栈**：FastAPI、SQLModel、异步处理
5. **完整的监控体系**：指标收集、结构化日志、健康检查

### 13.2 质量保证

- **测试覆盖率**：目标≥80%
- **代码质量**：Ruff格式化、MyPy类型检查
- **性能监控**：Prometheus指标、APM追踪
- **安全设计**：认证授权、数据加密、审计日志

### 13.3 扩展性设计

- **插件化架构**：支持自定义过滤器、转换器、目标
- **配置驱动**：通过JSON配置扩展功能
- **微服务就绪**：松耦合设计，易于拆分为微服务
- **云原生支持**：Docker容器化、Kubernetes部署

通过遵循本设计文档，开发团队可以构建出一个高质量、高性能、易维护的医疗数据集成平台。