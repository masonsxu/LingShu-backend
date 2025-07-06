import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.infrastructure.database import get_session
from app.main import app

# 创建测试用的文件数据库
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
    os.remove("./test.db")


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
