# LingShu - 医疗数据集成平台 (后端)

## 项目简介

LingShu 是一个现代化的、可视化的医疗数据集成平台。此仓库包含 LingShu 平台的后端服务，负责处理数据通道的创建、管理和消息处理。

## 技术栈

*   **Web 框架**: FastAPI
*   **ORM**: SQLModel
*   **数据库**: SQLite (开发环境)
*   **架构**: 领域驱动设计 (DDD)
*   **开发实践**: 测试驱动开发 (TDD)

## 架构概览 (领域驱动设计)

本项目采用领域驱动设计 (DDD) 的分层架构，以确保代码质量、可扩展性和可维护性：

*   **API 层 (`app/api`)**: 处理 HTTP 请求和响应，作为应用入口。
*   **应用层 (`app/application`)**: 编排领域对象以实现用例。
*   **领域层 (`app/domain`)**: 包含核心业务逻辑、领域模型和仓库接口。
*   **基础设施层 (`app/infrastructure`)**: 实现外部依赖，如数据库操作。

## 快速开始 (开发环境)

1.  **克隆仓库**:
    ```bash
    git clone git@github.com:masonsxu/LingShu-backend.git
    cd LingShu-backend
    ```
2.  **安装依赖**:
    ```bash
    uv pip install -r requirements.txt
    ```
3.  **运行应用**:
    ```bash
    uvicorn app.main:app --reload
    ```
    应用将在 `http://127.0.0.1:8000` 运行。API 文档可在 `http://127.0.0.1:8000/docs` 查看。

## 开发指南

本项目严格遵循测试驱动开发 (TDD) 实践。在贡献代码之前，请务必阅读并理解 `.cursorrules` 文件中的开发规范。

## 许可证

[待定]
