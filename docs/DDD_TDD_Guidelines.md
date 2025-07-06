# LingShu项目 - DDD+TDD开发规范与质量保证策略

## 1. 开发规范概述

### 1.1 核心原则
- **领域驱动设计(DDD)**：以业务领域为中心组织代码
- **测试驱动开发(TDD)**：先写测试，后写实现
- **持续集成(CI)**：代码提交后自动运行测试
- **代码评审**：所有代码必须经过peer review
- **质量第一**：宁可进度慢，不可质量差

### 1.2 质量目标
- **测试覆盖率**：≥80%
- **代码质量**：Ruff检查通过率100%
- **类型检查**：MyPy检查通过率100%
- **构建成功率**：≥99%
- **部署成功率**：≥99%

## 2. DDD架构规范

### 2.1 目录结构规范
```
app/
├── api/                    # API层：HTTP接口
│   ├── __init__.py
│   ├── dependencies.py     # 依赖注入
│   ├── routers.py         # 路由定义
│   └── models/            # 请求响应模型
│       ├── __init__.py
│       ├── channel.py     # 通道相关API模型
│       └── user.py        # 用户相关API模型
├── application/           # 应用层：业务流程编排
│   ├── __init__.py
│   ├── services/          # 应用服务
│   │   ├── __init__.py
│   │   ├── channel_service.py
│   │   └── user_service.py
│   └── use_cases/         # 用例
│       ├── __init__.py
│       ├── create_channel.py
│       └── process_message.py
├── domain/                # 领域层：核心业务逻辑
│   ├── __init__.py
│   ├── models/            # 领域模型
│   │   ├── __init__.py
│   │   ├── channel.py
│   │   └── user.py
│   ├── services/          # 领域服务
│   │   ├── __init__.py
│   │   └── channel_validation.py
│   ├── repositories/      # 仓储接口
│   │   ├── __init__.py
│   │   ├── channel_repository.py
│   │   └── user_repository.py
│   ├── events/            # 领域事件
│   │   ├── __init__.py
│   │   └── channel_events.py
│   └── exceptions/        # 领域异常
│       ├── __init__.py
│       └── channel_exceptions.py
└── infrastructure/        # 基础设施层：技术实现
    ├── __init__.py
    ├── database/          # 数据库
    │   ├── __init__.py
    │   ├── connection.py
    │   └── repositories/  # 仓储实现
    │       ├── __init__.py
    │       ├── channel_repository.py
    │       └── user_repository.py
    ├── external/          # 外部服务
    │   ├── __init__.py
    │   └── http_client.py
    └── config/            # 配置管理
        ├── __init__.py
        └── settings.py
```

### 2.2 分层职责定义

#### 2.2.1 API层职责
- **请求处理**：接收HTTP请求，参数验证
- **响应格式化**：将结果转换为HTTP响应
- **错误处理**：统一的异常处理和错误响应
- **文档生成**：API文档自动生成

```python
# app/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.models.channel import ChannelCreateRequest, ChannelResponse
from app.application.services.channel_service import ChannelService
from app.api.dependencies import get_channel_service

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])

@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    request: ChannelCreateRequest,
    channel_service: ChannelService = Depends(get_channel_service)
) -> ChannelResponse:
    """创建通道API端点"""
    try:
        channel = await channel_service.create_channel(request)
        return ChannelResponse.from_domain_model(channel)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### 2.2.2 应用层职责
- **业务流程编排**：协调多个领域对象完成业务用例
- **事务管理**：确保业务操作的原子性
- **权限检查**：验证用户权限
- **事件发布**：发布领域事件

```python
# app/application/services/channel_service.py
from typing import List
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository
from app.domain.services.channel_validation import ChannelValidationService
from app.domain.events.channel_events import ChannelCreatedEvent
from app.infrastructure.events.event_publisher import EventPublisher

class ChannelService:
    """通道应用服务"""
    
    def __init__(
        self,
        channel_repo: ChannelRepository,
        validation_service: ChannelValidationService,
        event_publisher: EventPublisher
    ):
        self.channel_repo = channel_repo
        self.validation_service = validation_service
        self.event_publisher = event_publisher
    
    async def create_channel(self, request: ChannelCreateRequest) -> ChannelModel:
        """创建通道用例"""
        # 1. 转换为领域模型
        channel = ChannelModel.from_create_request(request)
        
        # 2. 业务验证
        await self.validation_service.validate_channel_creation(channel)
        
        # 3. 持久化
        created_channel = await self.channel_repo.add(channel)
        
        # 4. 发布事件
        event = ChannelCreatedEvent(channel_id=created_channel.id)
        await self.event_publisher.publish(event)
        
        return created_channel
```

#### 2.2.3 领域层职责
- **业务规则**：封装核心业务逻辑和规则
- **数据完整性**：确保领域对象的一致性
- **领域专用语言**：使用业务术语命名
- **不变性保证**：维护业务不变性

```python
# app/domain/models/channel.py
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.domain.exceptions.channel_exceptions import InvalidChannelConfigError

class ChannelModel(BaseModel):
    """通道领域模型"""
    
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    enabled: bool = True
    source: SourceConfig
    destinations: List[DestinationConfig] = Field(min_items=1)
    filters: Optional[List[FilterConfig]] = None
    transformers: Optional[List[TransformerConfig]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('destinations')
    def validate_destinations(cls, v):
        """验证目标配置"""
        if not v:
            raise InvalidChannelConfigError("通道必须至少有一个目标")
        return v
    
    def enable(self) -> None:
        """启用通道"""
        self.enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable(self) -> None:
        """禁用通道"""
        self.enabled = False
        self.updated_at = datetime.utcnow()
    
    def can_process_message(self) -> bool:
        """检查是否可以处理消息"""
        return self.enabled and len(self.destinations) > 0
```

#### 2.2.4 基础设施层职责
- **数据持久化**：数据库操作的具体实现
- **外部服务集成**：HTTP客户端、消息队列等
- **配置管理**：环境变量、配置文件管理
- **技术工具**：日志、监控、缓存等

```python
# app/infrastructure/database/repositories/channel_repository.py
from typing import List, Optional
from sqlmodel import Session, select
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository

class SQLChannelRepository(ChannelRepository):
    """通道仓储SQL实现"""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def add(self, channel: ChannelModel) -> ChannelModel:
        """添加通道"""
        db_channel = ChannelModel.from_domain_model(channel)
        self.session.add(db_channel)
        await self.session.commit()
        await self.session.refresh(db_channel)
        return db_channel.to_domain_model()
    
    async def get_by_id(self, channel_id: str) -> Optional[ChannelModel]:
        """根据ID获取通道"""
        statement = select(ChannelModel).where(ChannelModel.id == channel_id)
        result = await self.session.exec(statement)
        db_channel = result.first()
        return db_channel.to_domain_model() if db_channel else None
```

## 3. TDD开发流程

### 3.1 Red-Green-Refactor循环

#### 3.1.1 Red阶段：编写失败的测试
```python
# tests/domain/test_channel_model.py
import pytest
from app.domain.models.channel import ChannelModel
from app.domain.exceptions.channel_exceptions import InvalidChannelConfigError

class TestChannelModel:
    """通道模型测试"""
    
    def test_channel_creation_with_valid_data(self):
        """测试使用有效数据创建通道"""
        # 这个测试一开始会失败，因为还没有实现
        channel = ChannelModel(
            name="Test Channel",
            source=HTTPSourceConfig(path="/test", method="POST"),
            destinations=[HTTPDestinationConfig(url="http://example.com")]
        )
        
        assert channel.name == "Test Channel"
        assert channel.enabled is True
        assert channel.can_process_message() is True
    
    def test_channel_creation_without_destinations_raises_error(self):
        """测试没有目标的通道创建失败"""
        with pytest.raises(InvalidChannelConfigError, match="通道必须至少有一个目标"):
            ChannelModel(
                name="Test Channel",
                source=HTTPSourceConfig(path="/test", method="POST"),
                destinations=[]
            )
```

#### 3.1.2 Green阶段：编写最小可行代码
```python
# app/domain/models/channel.py
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from app.domain.exceptions.channel_exceptions import InvalidChannelConfigError

class ChannelModel(BaseModel):
    """通道领域模型"""
    
    name: str = Field(..., min_length=1, max_length=100)
    enabled: bool = True
    source: SourceConfig
    destinations: List[DestinationConfig] = Field(min_items=1)
    
    @validator('destinations')
    def validate_destinations(cls, v):
        """验证目标配置"""
        if not v:
            raise InvalidChannelConfigError("通道必须至少有一个目标")
        return v
    
    def can_process_message(self) -> bool:
        """检查是否可以处理消息"""
        return self.enabled and len(self.destinations) > 0
```

#### 3.1.3 Refactor阶段：重构改进代码
```python
# app/domain/models/channel.py（重构后）
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.domain.exceptions.channel_exceptions import InvalidChannelConfigError
from app.domain.models.source_config import SourceConfig
from app.domain.models.destination_config import DestinationConfig

class ChannelModel(BaseModel):
    """通道领域模型
    
    通道是数据流转的基本单位，包含数据源、目标和处理规则。
    """
    
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100, description="通道名称")
    description: Optional[str] = Field(None, max_length=500, description="通道描述")
    enabled: bool = Field(True, description="是否启用")
    source: SourceConfig = Field(..., description="数据源配置")
    destinations: List[DestinationConfig] = Field(min_items=1, description="目标配置列表")
    filters: Optional[List[FilterConfig]] = Field(None, description="过滤器配置")
    transformers: Optional[List[TransformerConfig]] = Field(None, description="转换器配置")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('destinations')
    def validate_destinations(cls, v):
        """验证目标配置"""
        if not v:
            raise InvalidChannelConfigError("通道必须至少有一个目标")
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """验证通道名称"""
        if not v or v.strip() == "":
            raise InvalidChannelConfigError("通道名称不能为空")
        return v.strip()
    
    def enable(self) -> None:
        """启用通道"""
        self.enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable(self) -> None:
        """禁用通道"""
        self.enabled = False
        self.updated_at = datetime.utcnow()
    
    def can_process_message(self) -> bool:
        """检查是否可以处理消息"""
        return self.enabled and len(self.destinations) > 0
    
    def add_destination(self, destination: DestinationConfig) -> None:
        """添加目标"""
        if destination not in self.destinations:
            self.destinations.append(destination)
            self.updated_at = datetime.utcnow()
    
    def remove_destination(self, destination: DestinationConfig) -> None:
        """移除目标"""
        if destination in self.destinations:
            if len(self.destinations) <= 1:
                raise InvalidChannelConfigError("通道必须至少保留一个目标")
            self.destinations.remove(destination)
            self.updated_at = datetime.utcnow()
```

### 3.2 测试分层策略

#### 3.2.1 单元测试（70%）
```python
# tests/domain/test_channel_model.py
import pytest
from datetime import datetime
from app.domain.models.channel import ChannelModel
from app.domain.models.source_config import HTTPSourceConfig
from app.domain.models.destination_config import HTTPDestinationConfig
from app.domain.exceptions.channel_exceptions import InvalidChannelConfigError

class TestChannelModel:
    """通道模型单元测试"""
    
    @pytest.fixture
    def valid_channel_data(self):
        """有效的通道数据"""
        return {
            "name": "Test Channel",
            "description": "Test Description",
            "source": HTTPSourceConfig(path="/test", method="POST"),
            "destinations": [
                HTTPDestinationConfig(url="http://example.com/webhook")
            ]
        }
    
    def test_channel_creation_with_valid_data(self, valid_channel_data):
        """测试使用有效数据创建通道"""
        channel = ChannelModel(**valid_channel_data)
        
        assert channel.name == "Test Channel"
        assert channel.description == "Test Description"
        assert channel.enabled is True
        assert len(channel.destinations) == 1
        assert channel.can_process_message() is True
    
    def test_channel_creation_without_destinations_raises_error(self):
        """测试没有目标的通道创建失败"""
        with pytest.raises(InvalidChannelConfigError, match="通道必须至少有一个目标"):
            ChannelModel(
                name="Test Channel",
                source=HTTPSourceConfig(path="/test", method="POST"),
                destinations=[]
            )
    
    def test_channel_enable_disable(self, valid_channel_data):
        """测试通道启用和禁用"""
        channel = ChannelModel(**valid_channel_data)
        
        # 测试禁用
        channel.disable()
        assert channel.enabled is False
        assert channel.can_process_message() is False
        assert channel.updated_at is not None
        
        # 测试启用
        channel.enable()
        assert channel.enabled is True
        assert channel.can_process_message() is True
    
    def test_add_destination(self, valid_channel_data):
        """测试添加目标"""
        channel = ChannelModel(**valid_channel_data)
        new_destination = HTTPDestinationConfig(url="http://example2.com/webhook")
        
        channel.add_destination(new_destination)
        
        assert len(channel.destinations) == 2
        assert new_destination in channel.destinations
        assert channel.updated_at is not None
    
    def test_remove_destination_with_multiple_destinations(self, valid_channel_data):
        """测试移除目标（多个目标时）"""
        channel = ChannelModel(**valid_channel_data)
        second_destination = HTTPDestinationConfig(url="http://example2.com/webhook")
        channel.add_destination(second_destination)
        
        channel.remove_destination(second_destination)
        
        assert len(channel.destinations) == 1
        assert second_destination not in channel.destinations
    
    def test_remove_last_destination_raises_error(self, valid_channel_data):
        """测试移除最后一个目标时抛出错误"""
        channel = ChannelModel(**valid_channel_data)
        
        with pytest.raises(InvalidChannelConfigError, match="通道必须至少保留一个目标"):
            channel.remove_destination(channel.destinations[0])
    
    def test_channel_name_validation(self):
        """测试通道名称验证"""
        # 测试空名称
        with pytest.raises(InvalidChannelConfigError, match="通道名称不能为空"):
            ChannelModel(
                name="",
                source=HTTPSourceConfig(path="/test", method="POST"),
                destinations=[HTTPDestinationConfig(url="http://example.com")]
            )
        
        # 测试只有空格的名称
        with pytest.raises(InvalidChannelConfigError, match="通道名称不能为空"):
            ChannelModel(
                name="   ",
                source=HTTPSourceConfig(path="/test", method="POST"),
                destinations=[HTTPDestinationConfig(url="http://example.com")]
            )
```

#### 3.2.2 集成测试（20%）
```python
# tests/integration/test_channel_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.application.services.channel_service import ChannelService
from app.domain.models.channel import ChannelModel
from app.domain.repositories.channel_repository import ChannelRepository
from app.domain.services.channel_validation import ChannelValidationService
from app.infrastructure.events.event_publisher import EventPublisher

class TestChannelServiceIntegration:
    """通道服务集成测试"""
    
    @pytest.fixture
    def mock_channel_repository(self):
        """模拟通道仓储"""
        repo = Mock(spec=ChannelRepository)
        repo.add = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_name = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_validation_service(self):
        """模拟验证服务"""
        service = Mock(spec=ChannelValidationService)
        service.validate_channel_creation = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_event_publisher(self):
        """模拟事件发布器"""
        publisher = Mock(spec=EventPublisher)
        publisher.publish = AsyncMock()
        return publisher
    
    @pytest.fixture
    def channel_service(self, mock_channel_repository, mock_validation_service, mock_event_publisher):
        """通道服务实例"""
        return ChannelService(
            channel_repo=mock_channel_repository,
            validation_service=mock_validation_service,
            event_publisher=mock_event_publisher
        )
    
    @pytest.mark.asyncio
    async def test_create_channel_success(self, channel_service, mock_channel_repository, mock_validation_service, mock_event_publisher):
        """测试创建通道成功流程"""
        # 准备测试数据
        channel_data = {
            "name": "Test Channel",
            "source": HTTPSourceConfig(path="/test", method="POST"),
            "destinations": [HTTPDestinationConfig(url="http://example.com")]
        }
        
        expected_channel = ChannelModel(**channel_data)
        expected_channel.id = "test-channel-id"
        
        # 设置模拟
        mock_validation_service.validate_channel_creation.return_value = None
        mock_channel_repository.add.return_value = expected_channel
        
        # 执行测试
        result = await channel_service.create_channel(channel_data)
        
        # 验证结果
        assert result.id == "test-channel-id"
        assert result.name == "Test Channel"
        
        # 验证调用
        mock_validation_service.validate_channel_creation.assert_called_once()
        mock_channel_repository.add.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_channel_validation_failure(self, channel_service, mock_validation_service):
        """测试创建通道验证失败"""
        # 设置验证失败
        mock_validation_service.validate_channel_creation.side_effect = InvalidChannelConfigError("验证失败")
        
        # 执行测试并验证异常
        with pytest.raises(InvalidChannelConfigError, match="验证失败"):
            await channel_service.create_channel({
                "name": "Invalid Channel",
                "source": HTTPSourceConfig(path="/test", method="POST"),
                "destinations": [HTTPDestinationConfig(url="http://example.com")]
            })
```

#### 3.2.3 端到端测试（10%）
```python
# tests/e2e/test_channel_crud.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestChannelCRUDE2E:
    """通道CRUD端到端测试"""
    
    @pytest.fixture
    async def client(self):
        """测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_channel_full_lifecycle(self, client):
        """测试通道完整生命周期"""
        # 1. 创建通道
        channel_data = {
            "name": "E2E Test Channel",
            "description": "End-to-end test channel",
            "source": {
                "type": "http",
                "path": "/e2e-test",
                "method": "POST"
            },
            "destinations": [{
                "type": "http",
                "url": "http://example.com/webhook"
            }]
        }
        
        create_response = await client.post("/api/v1/channels", json=channel_data)
        assert create_response.status_code == 201
        
        created_channel = create_response.json()
        channel_id = created_channel["id"]
        
        # 2. 获取通道
        get_response = await client.get(f"/api/v1/channels/{channel_id}")
        assert get_response.status_code == 200
        
        retrieved_channel = get_response.json()
        assert retrieved_channel["name"] == "E2E Test Channel"
        assert retrieved_channel["enabled"] is True
        
        # 3. 更新通道
        update_data = {
            "name": "Updated E2E Test Channel",
            "description": "Updated description"
        }
        
        update_response = await client.put(f"/api/v1/channels/{channel_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_channel = update_response.json()
        assert updated_channel["name"] == "Updated E2E Test Channel"
        assert updated_channel["description"] == "Updated description"
        
        # 4. 禁用通道
        disable_response = await client.put(f"/api/v1/channels/{channel_id}/disable")
        assert disable_response.status_code == 200
        
        disabled_channel = disable_response.json()
        assert disabled_channel["enabled"] is False
        
        # 5. 删除通道
        delete_response = await client.delete(f"/api/v1/channels/{channel_id}")
        assert delete_response.status_code == 204
        
        # 6. 验证删除
        get_deleted_response = await client.get(f"/api/v1/channels/{channel_id}")
        assert get_deleted_response.status_code == 404
```

### 3.3 测试数据管理

#### 3.3.1 测试夹具（Fixtures）
```python
# tests/fixtures/channel_fixtures.py
import pytest
from typing import Dict, Any
from app.domain.models.channel import ChannelModel
from app.domain.models.source_config import HTTPSourceConfig, TCPSourceConfig
from app.domain.models.destination_config import HTTPDestinationConfig, TCPDestinationConfig

@pytest.fixture
def http_source_config():
    """HTTP源配置夹具"""
    return HTTPSourceConfig(
        path="/api/messages",
        method="POST",
        headers={"Content-Type": "application/json"}
    )

@pytest.fixture
def tcp_source_config():
    """TCP源配置夹具"""
    return TCPSourceConfig(
        host="0.0.0.0",
        port=8080,
        use_mllp=True
    )

@pytest.fixture
def http_destination_config():
    """HTTP目标配置夹具"""
    return HTTPDestinationConfig(
        url="http://localhost:8080/webhook",
        method="POST",
        headers={"Content-Type": "application/json"}
    )

@pytest.fixture
def tcp_destination_config():
    """TCP目标配置夹具"""
    return TCPDestinationConfig(
        host="localhost",
        port=8081,
        use_mllp=True
    )

@pytest.fixture
def basic_channel_data(http_source_config, http_destination_config):
    """基础通道数据夹具"""
    return {
        "name": "Test Channel",
        "description": "Test channel for unit testing",
        "source": http_source_config,
        "destinations": [http_destination_config]
    }

@pytest.fixture
def sample_channel(basic_channel_data):
    """示例通道夹具"""
    return ChannelModel(**basic_channel_data)

@pytest.fixture
def complex_channel_data(http_source_config, http_destination_config, tcp_destination_config):
    """复杂通道数据夹具"""
    return {
        "name": "Complex Test Channel",
        "description": "Complex channel with multiple destinations",
        "source": http_source_config,
        "destinations": [http_destination_config, tcp_destination_config],
        "filters": [{
            "type": "python_script",
            "script": "_passed = 'test' in message.get('content', '')"
        }],
        "transformers": [{
            "type": "python_script",
            "script": "_transformed_message = {'processed': True, 'original': message}"
        }]
    }
```

#### 3.3.2 测试数据构建器
```python
# tests/builders/channel_builder.py
from typing import List, Optional
from app.domain.models.channel import ChannelModel
from app.domain.models.source_config import SourceConfig, HTTPSourceConfig
from app.domain.models.destination_config import DestinationConfig, HTTPDestinationConfig

class ChannelBuilder:
    """通道构建器，用于测试数据构建"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置构建器"""
        self._id: Optional[str] = None
        self._name: str = "Test Channel"
        self._description: Optional[str] = None
        self._enabled: bool = True
        self._source: Optional[SourceConfig] = None
        self._destinations: List[DestinationConfig] = []
        self._filters: List[dict] = []
        self._transformers: List[dict] = []
        return self
    
    def with_id(self, id: str):
        """设置ID"""
        self._id = id
        return self
    
    def with_name(self, name: str):
        """设置名称"""
        self._name = name
        return self
    
    def with_description(self, description: str):
        """设置描述"""
        self._description = description
        return self
    
    def disabled(self):
        """设置为禁用状态"""
        self._enabled = False
        return self
    
    def with_http_source(self, path: str = "/test", method: str = "POST"):
        """设置HTTP源"""
        self._source = HTTPSourceConfig(path=path, method=method)
        return self
    
    def with_http_destination(self, url: str = "http://example.com/webhook"):
        """添加HTTP目标"""
        self._destinations.append(HTTPDestinationConfig(url=url))
        return self
    
    def with_filter(self, filter_type: str, script: str):
        """添加过滤器"""
        self._filters.append({
            "type": filter_type,
            "script": script
        })
        return self
    
    def with_transformer(self, transformer_type: str, script: str):
        """添加转换器"""
        self._transformers.append({
            "type": transformer_type,
            "script": script
        })
        return self
    
    def build(self) -> ChannelModel:
        """构建通道模型"""
        if not self._source:
            self._source = HTTPSourceConfig(path="/default", method="POST")
        
        if not self._destinations:
            self._destinations = [HTTPDestinationConfig(url="http://default.com")]
        
        return ChannelModel(
            id=self._id,
            name=self._name,
            description=self._description,
            enabled=self._enabled,
            source=self._source,
            destinations=self._destinations,
            filters=self._filters if self._filters else None,
            transformers=self._transformers if self._transformers else None
        )

# 使用示例
def test_channel_builder():
    """测试通道构建器"""
    channel = (ChannelBuilder()
              .with_name("Test Channel")
              .with_description("Test Description")
              .with_http_source("/api/test", "POST")
              .with_http_destination("http://test1.com")
              .with_http_destination("http://test2.com")
              .with_filter("python_script", "_passed = True")
              .disabled()
              .build())
    
    assert channel.name == "Test Channel"
    assert channel.enabled is False
    assert len(channel.destinations) == 2
```

## 4. 代码质量保证

### 4.1 静态代码分析

#### 4.1.1 Ruff配置
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
indent-width = 4
exclude = [".venv", "venv", "migrations", "__pycache__", "*.egg-info"]
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "W",     # pycodestyle warnings
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
    "A",     # flake8-builtins
    "C90",   # mccabe complexity
    "ASYNC", # flake8-async
    "S",     # flake8-bandit (security)
    "T20",   # flake8-print
    "PIE",   # flake8-pie
    "RET",   # flake8-return
    "ARG",   # flake8-unused-arguments
    "PTH",   # flake8-use-pathlib
    "ERA",   # eradicate
]

ignore = [
    "B008",  # FastAPI依赖注入场景下，忽略这个报错
    "S101",  # 允许使用assert，在测试中很常见
    "T201",  # 允许print语句，在某些场景下有用
    "ARG002", # 允许未使用的方法参数
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "ARG001", "ARG002"]  # 测试文件的特殊规则

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true
skip-magic-trailing-comma = false

[tool.ruff.lint.isort]
known-first-party = ["app", "tests"]
combine-as-imports = true
force-single-line = false
```

#### 4.1.2 MyPy配置
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_unreachable = true
strict_equality = true

# 第三方库类型
[[tool.mypy.overrides]]
module = [
    "uvicorn.*",
    "fastapi.*",
    "sqlmodel.*",
    "pydantic.*",
]
ignore_missing_imports = true

# 测试文件的类型检查
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### 4.2 代码审查规范

#### 4.2.1 Pull Request模板
```markdown
## 变更描述
<!-- 简要描述这次变更的内容和目的 -->

## 变更类型
- [ ] 新功能 (feature)
- [ ] 修复bug (fix)
- [ ] 文档更新 (docs)
- [ ] 代码重构 (refactor)
- [ ] 性能优化 (perf)
- [ ] 测试相关 (test)
- [ ] 构建/工具 (build/tool)

## 测试
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成
- [ ] 测试覆盖率 ≥ 80%

## 代码质量
- [ ] Ruff检查通过
- [ ] MyPy类型检查通过
- [ ] 代码遵循项目规范
- [ ] 已添加必要的文档和注释

## 安全性
- [ ] 没有引入安全漏洞
- [ ] 敏感信息已妥善处理
- [ ] 输入验证已实现

## 性能
- [ ] 没有明显的性能问题
- [ ] 数据库查询已优化
- [ ] 内存使用合理

## 部署
- [ ] 数据库迁移已准备
- [ ] 配置变更已说明
- [ ] 向后兼容性已考虑

## 截图/日志
<!-- 如有必要，请提供相关截图或日志 -->

## 相关Issue
<!-- 关联的Issue编号，如 #123 -->
```

#### 4.2.2 代码审查清单
```markdown
# 代码审查清单

## 代码结构
- [ ] 代码符合DDD分层架构
- [ ] 类和方法职责单一
- [ ] 依赖注入正确使用
- [ ] 异常处理合理

## 业务逻辑
- [ ] 业务规则正确实现
- [ ] 边界条件已考虑
- [ ] 数据验证充分
- [ ] 错误处理完整

## 测试覆盖
- [ ] 单元测试覆盖核心逻辑
- [ ] 集成测试覆盖关键流程
- [ ] 异常情况有测试
- [ ] 测试用例有意义

## 性能考虑
- [ ] 数据库查询优化
- [ ] 避免N+1查询
- [ ] 异步处理适当
- [ ] 缓存策略合理

## 安全考虑
- [ ] 输入验证和清理
- [ ] 权限检查完整
- [ ] 敏感数据保护
- [ ] SQL注入防护

## 可维护性
- [ ] 代码可读性良好
- [ ] 注释和文档充分
- [ ] 命名规范一致
- [ ] 复杂度合理
```

## 5. 持续集成配置

### 5.1 GitHub Actions工作流

#### 5.1.1 主要工作流
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.12'
  
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
        ports:
          - 5432:5432
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          echo "Running Ruff linting..."
          ruff check app/ tests/
          echo "Running Ruff formatting check..."
          ruff format --check app/ tests/
      
      - name: Run type checking
        run: |
          echo "Running MyPy type checking..."
          mypy app/ tests/
      
      - name: Run security check
        run: |
          echo "Running Bandit security check..."
          bandit -r app/ -f json -o bandit-report.json
        continue-on-error: true
      
      - name: Run unit tests
        run: |
          echo "Running unit tests..."
          pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=term-missing
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      
      - name: Run integration tests
        run: |
          echo "Running integration tests..."
          pytest tests/integration/ -v --cov=app --cov-append --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      
      - name: Run end-to-end tests
        run: |
          echo "Running end-to-end tests..."
          pytest tests/e2e/ -v --cov=app --cov-append --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: |
            coverage.xml
            bandit-report.json
```

#### 5.1.2 部署工作流
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # 这里添加实际的部署脚本
      
      - name: Run smoke tests
        run: |
          echo "Running smoke tests..."
          # 这里添加冒烟测试
      
      - name: Deploy to production
        if: success()
        run: |
          echo "Deploying to production environment..."
          # 这里添加生产部署脚本
```

### 5.2 质量门禁

#### 5.2.1 质量门禁配置
```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Check test coverage
        run: |
          pytest --cov=app --cov-report=json
          python scripts/check_coverage.py --min-coverage 80
      
      - name: Check code complexity
        run: |
          python scripts/check_complexity.py --max-complexity 10
      
      - name: Check dependencies
        run: |
          pip-audit --desc --format=json --output=audit-report.json
          python scripts/check_vulnerabilities.py
      
      - name: Performance regression test
        run: |
          python scripts/performance_test.py --baseline main
```

#### 5.2.2 质量检查脚本
```python
# scripts/check_coverage.py
import json
import sys
import argparse

def check_coverage(min_coverage: float) -> bool:
    """检查测试覆盖率"""
    try:
        with open('coverage.json', 'r') as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data['totals']['percent_covered']
        
        print(f"当前测试覆盖率: {total_coverage:.2f}%")
        print(f"最低要求覆盖率: {min_coverage:.2f}%")
        
        if total_coverage < min_coverage:
            print(f"❌ 测试覆盖率不足，需要至少 {min_coverage}%")
            return False
        
        print("✅ 测试覆盖率达标")
        return True
        
    except FileNotFoundError:
        print("❌ 未找到覆盖率报告文件")
        return False
    except Exception as e:
        print(f"❌ 检查覆盖率时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='检查测试覆盖率')
    parser.add_argument('--min-coverage', type=float, default=80.0,
                       help='最低覆盖率要求 (默认: 80.0)')
    
    args = parser.parse_args()
    
    if not check_coverage(args.min_coverage):
        sys.exit(1)

if __name__ == "__main__":
    main()
```

```python
# scripts/check_complexity.py
import ast
import sys
import argparse
from pathlib import Path

class ComplexityVisitor(ast.NodeVisitor):
    """代码复杂度检查访问器"""
    
    def __init__(self):
        self.complexity_violations = []
    
    def visit_FunctionDef(self, node):
        """检查函数复杂度"""
        complexity = self.calculate_complexity(node)
        if complexity > self.max_complexity:
            self.complexity_violations.append({
                'function': node.name,
                'line': node.lineno,
                'complexity': complexity
            })
        self.generic_visit(node)
    
    def calculate_complexity(self, node):
        """计算循环复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def set_max_complexity(self, max_complexity):
        """设置最大复杂度"""
        self.max_complexity = max_complexity

def check_complexity(max_complexity: int) -> bool:
    """检查代码复杂度"""
    violations = []
    
    # 检查app目录下的所有Python文件
    for py_file in Path('app').rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            visitor = ComplexityVisitor()
            visitor.set_max_complexity(max_complexity)
            visitor.visit(tree)
            
            for violation in visitor.complexity_violations:
                violations.append({
                    'file': str(py_file),
                    'function': violation['function'],
                    'line': violation['line'],
                    'complexity': violation['complexity']
                })
        
        except Exception as e:
            print(f"警告: 无法解析文件 {py_file}: {e}")
    
    if violations:
        print(f"❌ 发现 {len(violations)} 个复杂度违规:")
        for violation in violations:
            print(f"  {violation['file']}:{violation['line']} "
                  f"函数 {violation['function']} 复杂度 {violation['complexity']} "
                  f"(最大允许: {max_complexity})")
        return False
    
    print("✅ 代码复杂度检查通过")
    return True

def main():
    parser = argparse.ArgumentParser(description='检查代码复杂度')
    parser.add_argument('--max-complexity', type=int, default=10,
                       help='最大复杂度 (默认: 10)')
    
    args = parser.parse_args()
    
    if not check_complexity(args.max_complexity):
        sys.exit(1)

if __name__ == "__main__":
    main()
```
