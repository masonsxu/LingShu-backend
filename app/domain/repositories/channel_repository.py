from typing import List, Optional
from sqlmodel import Session, select
from app.domain.models.channel import ChannelModel

class ChannelRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, channel_id: str) -> Optional[ChannelModel]:
        return self.session.get(ChannelModel, channel_id)

    def get_all(self) -> List[ChannelModel]:
        return self.session.exec(select(ChannelModel)).all()

    def add(self, channel: ChannelModel) -> ChannelModel:
        self.session.add(channel)
        self.session.commit()
        self.session.refresh(channel)
        return channel 