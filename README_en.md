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
    The application will be running at `http://127.0.0.1:8000`. API documentation is available at `http://127.0.0.1:8000/docs`.

## Development Guidelines

This project strictly adheres to Test-Driven Development (TDD) practices. Before contributing code, please make sure to read and understand the development guidelines in the `.cursorrules` file.

## License

[To be determined]
