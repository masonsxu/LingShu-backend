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

---

# LingShu - Healthcare Data Integration Platform (Backend)

## Project Overview

LingShu is a modern, visual platform for healthcare data integration. This repository contains the backend service for the LingShu platform, responsible for creating, managing, and processing messages through data channels.

## Technology Stack

*   **Web Framework**: FastAPI
*   **ORM**: SQLModel
*   **Database**: SQLite (for development)
*   **Architecture**: Domain-Driven Design (DDD)
*   **Development Practice**: Test-Driven Development (TDD)

## Architecture Overview (Domain-Driven Design)

This project adopts a layered architecture based on Domain-Driven Design (DDD) to ensure code quality, scalability, and maintainability:

*   **API Layer (`app/api`)**: Handles HTTP requests and responses, serving as the application's entry point.
*   **Application Layer (`app/application`)**: Orchestrates domain objects to fulfill application use cases.
*   **Domain Layer (`app/domain`)**: Contains the core business logic, domain models, and repository interfaces.
*   **Infrastructure Layer (`app/infrastructure`)**: Implements external dependencies, such as database operations.

## Quick Start (Development)

1.  **Clone the repository**:
    ```bash
    git clone git@github.com:masonsxu/LingShu-backend.git
    cd LingShu-backend
    ```
2.  **Install Dependencies**:
    ```bash
    uv pip install -r requirements.txt
    ```
3.  **Run the Application**:
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will be running at `http://127.00.1:8000`. API documentation is available at `http://127.0.0.1:8000/docs`.

## Development Guidelines

This project strictly adheres to Test-Driven Development (TDD) practices. Before contributing code, please make sure to read and understand the development guidelines in the `.cursorrules` file.

## License

[To be determined]
