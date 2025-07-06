"""通道相关的领域异常"""


class ChannelDomainError(Exception):
    """通道领域错误基类"""
    pass


class ChannelNotFoundError(ChannelDomainError):
    """通道不存在错误"""
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__(f"Channel with ID '{channel_id}' not found")


class ChannelAlreadyExistsError(ChannelDomainError):
    """通道已存在错误"""
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__(f"Channel with ID '{channel_id}' already exists")


class InvalidChannelDataError(ChannelDomainError):
    """无效通道数据错误"""
    def __init__(self, message: str):
        super().__init__(f"Invalid channel data: {message}")


class ChannelValidationError(ChannelDomainError):
    """通道验证错误"""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for field '{field}': {message}")


class ChannelOperationError(ChannelDomainError):
    """通道操作错误"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"Operation '{operation}' failed: {message}")