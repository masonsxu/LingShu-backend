# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LingShu is a healthcare data integration platform backend built with FastAPI and Domain-Driven Design (DDD) architecture. It provides a channel-based system for receiving, filtering, transforming, and distributing healthcare data messages.

## Architecture

The codebase follows DDD with clear separation of concerns:

- **API Layer** (`app/api/`): HTTP endpoints and request/response handling
- **Application Layer** (`app/application/`): Business logic orchestration and use cases
- **Domain Layer** (`app/domain/`): Core business models and repository interfaces
- **Infrastructure Layer** (`app/infrastructure/`): External dependencies like database

### Key Components

- **ChannelModel**: Core domain entity defining data flow configurations with source, filters, transformers, and destinations
- **ChannelProcessor**: Application service handling message processing pipeline
- **ChannelRepository**: Data access layer for channel persistence

## Common Development Commands

### Development Setup
```bash
# Install dependencies
uv pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_channels_api.py

# Run with coverage
pytest --cov=app
```

### Code Quality
```bash
# Lint code
ruff check

# Format code
ruff format

# Check specific files
ruff check app/main.py
```

## Key Technical Details

### Channel Configuration
Channels support multiple configuration types stored as JSON in SQLite:
- **Sources**: HTTP endpoints, TCP listeners (with optional MLLP)
- **Filters**: Python script-based message filtering
- **Transformers**: Python script-based message transformation
- **Destinations**: HTTP endpoints, TCP targets (with optional MLLP)

### Message Processing Pipeline
1. Message received via configured source
2. Applied through filters (message rejected if any filter fails)
3. Passed through transformers (message modified by scripts)
4. Distributed to all configured destinations

### Database
- Uses SQLite for development with SQLModel ORM
- Database tables created automatically on application startup
- Example channel seeded during application lifespan

## Development Practices

- Follow Test-Driven Development (TDD)
- Use pytest for testing with proper fixtures
- Maintain 100-character line length (configured in Ruff)
- Keep Chinese comments in domain models for business context
- All configuration models use Pydantic for validation