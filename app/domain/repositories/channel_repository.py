from typing import Optional, Sequence

from sqlmodel import Session, select

from app.domain.models.channel import ChannelModel


class ChannelRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, channel_id: str) -> Optional[ChannelModel]:
        return self.session.get(ChannelModel, channel_id)

    def get_all(self) -> Sequence[ChannelModel]:
        channels = self.session.exec(select(ChannelModel)).all()
        return channels

    def add(self, channel: ChannelModel) -> ChannelModel:
        # 构造用于数据库写入的 dict
        channel_data = channel.model_dump()
        # 这里所有嵌套的 Pydantic 对象都已被递归转为 dict
        db_channel = ChannelModel(**channel_data)
        self.session.add(db_channel)
        self.session.commit()
        self.session.refresh(db_channel)
        return db_channel
