import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app.infrastructure.database import get_session

# 创建测试用的内存数据库
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)

# 每次测试前自动建表和销毁表
def override_get_session():
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="function")
def client():
    return TestClient(app) 