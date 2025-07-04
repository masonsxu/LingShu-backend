from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """创建数据库表."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话."""
    with Session(engine) as session:
        yield session
