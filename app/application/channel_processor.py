from typing import Any

from fastapi import HTTPException, status
from loguru import logger

from app.domain.models.channel import (
    ChannelModel,
    HTTPDestinationConfig,
    PythonScriptFilterConfig,
    PythonScriptTransformerConfig,
    TCPDestinationConfig,
)
from app.domain.repositories.channel_repository import ChannelRepository

# 绑定模块名称到logger
app_logger = logger.bind(module=__name__)


class ChannelProcessor:
    """通道处理器：负责通道的创建校验、消息处理（过滤、转换、分发）等核心业务逻辑."""

    def __init__(self):
        """初始化通道处理器."""
        pass

    def create_channel_with_checks(
        self, channel: ChannelModel, repo: ChannelRepository
    ) -> ChannelModel:
        """创建通道前进行唯一性和参数校验。

        参数：
            channel: 待创建的通道对象。
            repo: 通道仓储实例。
        返回：
            创建成功的通道对象。
        异常：
            HTTPException: 若 id 缺失或已存在则抛出 400/409 错误。
        """
        if channel.id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel ID cannot be None.",
            )
        existing_channel = repo.get_by_id(channel.id)
        if existing_channel:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Channel with ID '{channel.id}' already exists.",
            )
        return repo.add(channel)

    async def process_message_with_checks(
        self, channel_id: str, message: Any, repo: ChannelRepository
    ) -> dict:
        """校验通道状态后处理消息。

        参数：
            channel_id: 通道唯一标识。
            message: 待处理消息。
            repo: 通道仓储实例。
        返回：
            处理结果字典。
        异常：
            HTTPException: 通道不存在或被禁用时抛出。
        """
        channel = repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
        if not channel.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Channel is disabled."
            )
        return await self.process_message(channel, message)

    async def process_message(self, channel: ChannelModel, message: Any) -> dict:
        """按通道配置依次执行过滤、转换、分发等处理流程。

        参数：
            channel: 通道对象。
            message: 原始消息。
        返回：
            处理结果字典，包括最终消息和各目标分发结果。
        """
        app_logger.info(f"Processing message for channel '{channel.name}' (ID: {channel.id})")
        current_message = message

        # 过滤
        filter_result = self._apply_filters(channel, current_message)
        if filter_result is not None:
            return filter_result
        current_message = filter_result

        # 转换
        transformer_result = self._apply_transformers(channel, current_message)
        if transformer_result is not None:
            return transformer_result
        current_message = transformer_result

        # 分发
        results = self._dispatch_to_destinations(channel, current_message)

        return {
            "status": "success",
            "processed_message": current_message,
            "destination_results": results,
        }

    def _apply_filters(self, channel: ChannelModel, message: Any) -> Any:
        """依次应用所有过滤器，若被过滤或出错则返回 dict，否则返回处理后的消息。"""
        if not channel.filters:
            return None
        for i, filter_config in enumerate(channel.filters):
            if not isinstance(filter_config, PythonScriptFilterConfig):
                continue
            script = filter_config.script
            app_logger.debug(f"Applying Python script filter {i} for channel '{channel.name}'")
            try:
                local_vars = {"message": message, "_passed": False}
                exec(script, {}, local_vars)
                if not local_vars.get("_passed", False):
                    app_logger.info(
                        f"Message filtered out by script {i} for channel '{channel.name}'"
                    )
                    return {
                        "status": "filtered",
                        "message": "Message filtered out.",
                    }
                message = local_vars.get("message", message)
            except Exception as e:
                app_logger.error(
                    f"Error executing filter script {i} for channel '{channel.name}': {e}"
                )
                return {
                    "status": "error",
                    "message": f"Filter script error: {e}",
                }

    def _apply_transformers(self, channel: ChannelModel, message: Any) -> Any:
        """依次应用所有转换器，若出错则返回 dict，否则返回处理后的消息。"""
        if not channel.transformers:
            return None

        for i, transformer_config in enumerate(channel.transformers):
            if not isinstance(transformer_config, PythonScriptTransformerConfig):
                continue
            script = transformer_config.script
            app_logger.debug(f"Applying Python script transformer {i} for channel '{channel.name}'")
            try:
                local_vars = {
                    "message": message,
                    "_transformed_message": None,
                }
                exec(script, {}, local_vars)
                if "_transformed_message" in local_vars:
                    message = local_vars["_transformed_message"]
                else:
                    app_logger.warning(
                        f"Transformer script {i} for channel '{channel.name}' "
                        "did not set '_transformed_message'. "
                        "Message remains unchanged."
                    )
            except Exception as e:
                app_logger.error(
                    f"Error executing transformer script {i} for channel '{channel.name}': {e}"
                )
                return {
                    "status": "error",
                    "message": f"Transformer script error: {e}",
                }

    def _dispatch_to_destinations(self, channel: ChannelModel, message: Any) -> list[dict]:
        """将消息分发到所有目标，返回分发结果列表。"""
        results = []
        for i, destination_config in enumerate(channel.destinations):
            app_logger.debug(f"Sending message to destination {i} for channel '{channel.name}'")
            app_logger.debug(f"Destination config type: {type(destination_config)}")
            app_logger.debug(f"Destination config: {destination_config}")

            try:
                result = self._send_to_single_destination(destination_config, message)
                results.append(result)
            except Exception as e:
                app_logger.error(
                    f"Error sending to destination {i} for channel '{channel.name}': {e}"
                )
                destination_type = self._get_destination_type(destination_config)
                results.append(
                    {
                        "destination_type": destination_type,
                        "status": "error",
                        "error": str(e),
                    }
                )
        return results

    def _send_to_single_destination(self, destination_config, message: Any) -> dict:
        """发送消息到单个目标"""
        # 首先尝试使用isinstance检查
        if isinstance(destination_config, HTTPDestinationConfig):
            return self._send_to_http_destination(destination_config, message)
        elif isinstance(destination_config, TCPDestinationConfig):
            return self._send_to_tcp_destination(destination_config, message)
        else:
            # 如果isinstance失败，尝试基于type字段处理
            return self._send_to_fallback_destination(destination_config, message)

    def _send_to_http_destination(self, destination_config, message: Any) -> dict:
        """发送到HTTP目标"""
        app_logger.info(
            "Simulating HTTP "
            f"{destination_config.method} to "
            f"{destination_config.url} with message: {message}"
        )
        return {
            "destination_type": "http",
            "status": "sent",
            "url": destination_config.url,
        }

    def _send_to_tcp_destination(self, destination_config, message: Any) -> dict:
        """发送到TCP目标"""
        app_logger.info(
            "Simulating TCP send to "
            f"{destination_config.host}:{destination_config.port} "
            f"with message: {message}"
        )
        return {
            "destination_type": "tcp",
            "status": "sent",
            "host": destination_config.host,
            "port": destination_config.port,
        }

    def _send_to_fallback_destination(self, destination_config, message: Any) -> dict:
        """处理未知类型的目标配置（回退方案）"""
        dest_type = self._get_destination_type(destination_config)

        if dest_type == "http" and hasattr(destination_config, "url"):
            # 手动处理HTTP目标
            app_logger.info(
                "Simulating HTTP (fallback) "
                f"{getattr(destination_config, 'method', 'POST')} to "
                f"{destination_config.url} with message: {message}"
            )
            return {
                "destination_type": "http",
                "status": "sent",
                "url": destination_config.url,
            }
        elif dest_type == "http" and isinstance(destination_config, dict):
            # 处理字典格式的HTTP目标
            app_logger.info(
                "Simulating HTTP (fallback dict) "
                f"{destination_config.get('method', 'POST')} to "
                f"{destination_config.get('url')} with message: {message}"
            )
            return {
                "destination_type": "http",
                "status": "sent",
                "url": destination_config.get("url"),
            }
        elif dest_type == "tcp" and hasattr(destination_config, "host"):
            # 手动处理TCP目标
            app_logger.info(
                "Simulating TCP (fallback) send to "
                f"{destination_config.host}:{destination_config.port} "
                f"with message: {message}"
            )
            return {
                "destination_type": "tcp",
                "status": "sent",
                "host": destination_config.host,
                "port": destination_config.port,
            }
        elif dest_type == "tcp" and isinstance(destination_config, dict):
            # 处理字典格式的TCP目标
            app_logger.info(
                "Simulating TCP (fallback dict) send to "
                f"{destination_config.get('host')}:{destination_config.get('port')} "
                f"with message: {message}"
            )
            return {
                "destination_type": "tcp",
                "status": "sent",
                "host": destination_config.get("host"),
                "port": destination_config.get("port"),
            }
        else:
            app_logger.warning(f"Unknown destination type: {dest_type or 'unknown'}")
            return {"destination_type": dest_type or "unknown", "status": "skipped"}

    def _get_destination_type(self, destination_config) -> str:
        """获取目标配置的类型"""
        if hasattr(destination_config, "type"):
            return destination_config.type
        elif isinstance(destination_config, dict):
            return destination_config.get("type", "unknown")
        else:
            return "unknown"
