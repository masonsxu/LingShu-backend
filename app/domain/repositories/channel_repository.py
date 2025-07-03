from typing import List, Optional
from sqlmodel import Session, select
from app.domain.models.channel import ChannelModel

class ChannelRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, channel_id: str) -> Optional[ChannelModel]:
        return self.session.get(ChannelModel, channel_id)

    def get_all(self) -> List[ChannelModel]:
        channels = self.session.exec(select(ChannelModel)).all()
        for channel in channels:
            # Manually convert JSON data to Pydantic models after retrieval
            if isinstance(channel.source, dict):
                channel.source = ChannelModel.model_validate(channel.model_dump()).source
            if channel.filters and isinstance(channel.filters, list):
                channel.filters = [ChannelModel.model_validate(channel.model_dump()).filters[i] for i, _ in enumerate(channel.filters)]
            if channel.transformers and isinstance(channel.transformers, list):
                channel.transformers = [ChannelModel.model_validate(channel.model_dump()).transformers[i] for i, _ in enumerate(channel.transformers)]
            if channel.destinations and isinstance(channel.destinations, list):
                channel.destinations = [ChannelModel.model_validate(channel.model_dump()).destinations[i] for i, _ in enumerate(channel.destinations)]
        return channels

    def add(self, channel: ChannelModel) -> ChannelModel:
        self.session.add(channel)
        self.session.commit()
        self.session.refresh(channel)
        return channel 