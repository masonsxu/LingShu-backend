from collections.abc import Sequence

from sqlmodel import Session, select

from app.domain.models.channel import ChannelModel


class ChannelRepository:
    """ChannelRepository 是 ChannelModel 的仓储类.

    用于从数据库获取通道或向数据库添加新通道.
    """

    def __init__(self, session: Session):
        """初始化 ChannelRepository.

        参数：
            session: 用于数据库操作的会话对象.

        """
        self.session = session

    def get_by_id(self, channel_id: str) -> ChannelModel | None:
        """根据 id 获取通道.

        参数：
            channel_id: 要获取的通道 id.

        返回：
            匹配的通道对象，若不存在则为 None.

        """
        return self.session.get(ChannelModel, channel_id)

    def get_all(self) -> Sequence[ChannelModel]:
        """获取所有通道.

        返回：
            所有通道对象的列表.

        """
        channels = self.session.exec(select(ChannelModel)).all()
        return channels

    def add(self, channel: ChannelModel) -> ChannelModel:
        """向数据库添加一个通道.

        参数：
            channel: 要添加的通道对象.

        返回：
            添加后的通道对象.

        """
        # 构造用于数据库写入的 dict
        channel_data = channel.model_dump()
        # 这里所有嵌套的 Pydantic 对象都已被递归转为 dict
        db_channel = ChannelModel(**channel_data)
        self.session.add(db_channel)
        self.session.commit()
        self.session.refresh(db_channel)
        return db_channel

    def update(self, channel: ChannelModel) -> ChannelModel:
        """更新通道.

        参数：
            channel: 要更新的通道对象.

        返回：
            更新后的通道对象.
        """
        db_channel = self.session.get(ChannelModel, channel.id)
        if not db_channel:
            raise ValueError(f"Channel with id {channel.id} not found")
        for field, value in channel.model_dump().items():
            setattr(db_channel, field, value)
        self.session.commit()
        self.session.refresh(db_channel)
        return db_channel

    def delete(self, channel_id: str) -> bool:
        """删除通道.

        参数：
            channel_id: 要删除的通道ID.

        返回：
            删除是否成功.
        """
        db_channel = self.session.get(ChannelModel, channel_id)
        if not db_channel:
            return False

        self.session.delete(db_channel)
        self.session.commit()
        return True
