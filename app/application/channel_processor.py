import logging
from typing import Any

from app.domain.models.channel import (
    ChannelModel,
    HTTPDestinationConfig,
    PythonScriptFilterConfig,
    PythonScriptTransformerConfig,
    TCPDestinationConfig,
)
from app.domain.repositories.channel_repository import ChannelRepository
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ChannelProcessor:
    def __init__(self):
        pass

    def create_channel_with_checks(
        self, channel: ChannelModel, repo: ChannelRepository
    ) -> ChannelModel:
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
        channel = repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found."
            )
        if not channel.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Channel is disabled."
            )
        return await self.process_message(channel, message)

    async def process_message(self, channel: ChannelModel, message: Any) -> dict:
        """Processes a message through the given channel's filters, transformers, and destinations."""
        logger.info(
            f"Processing message for channel '{channel.name}' (ID: {channel.id})"
        )
        current_message = message

        # --- Filters ---
        if channel.filters:
            for i, filter_config in enumerate(channel.filters):
                if isinstance(filter_config, PythonScriptFilterConfig):
                    script = filter_config.script
                    logger.debug(
                        f"Applying Python script filter {i} for channel '{channel.name}'"
                    )
                    try:
                        # WARNING: Executing arbitrary code from configuration is a security risk.
                        # In a production environment, this requires a secure sandboxing mechanism.
                        local_vars = {"message": current_message, "_passed": False}
                        exec(script, {}, local_vars)
                        if not local_vars.get("_passed", False):
                            logger.info(
                                f"Message filtered out by script {i} for channel '{channel.name}'"
                            )
                            return {
                                "status": "filtered",
                                "message": "Message filtered out.",
                            }
                        current_message = local_vars.get(
                            "message", current_message
                        )  # Allow script to modify message
                    except Exception as e:
                        logger.error(
                            f"Error executing filter script {i} for channel '{channel.name}': {e}"
                        )
                        return {
                            "status": "error",
                            "message": f"Filter script error: {e}",
                        }

        # --- Transformers ---
        if channel.transformers:
            for i, transformer_config in enumerate(channel.transformers):
                if isinstance(transformer_config, PythonScriptTransformerConfig):
                    script = transformer_config.script
                    logger.debug(
                        f"Applying Python script transformer {i} for channel '{channel.name}'"
                    )
                    try:
                        # WARNING: Executing arbitrary code from configuration is a security risk.
                        # In a production environment, this requires a secure sandboxing mechanism.
                        local_vars = {
                            "message": current_message,
                            "_transformed_message": None,
                        }
                        exec(script, {}, local_vars)
                        if "_transformed_message" in local_vars:
                            current_message = local_vars["_transformed_message"]
                        else:
                            logger.warning(
                                f"Transformer script {i} for channel '{channel.name}' did not set '_transformed_message'. Message remains unchanged."
                            )
                    except Exception as e:
                        logger.error(
                            f"Error executing transformer script {i} for channel '{channel.name}': {e}"
                        )
                        return {
                            "status": "error",
                            "message": f"Transformer script error: {e}",
                        }

        # --- Destinations ---
        results = []
        # Destinations are already validated Pydantic models, no need for additional validation

        for i, destination_config in enumerate(channel.destinations):
            logger.debug(
                f"Sending message to destination {i} for channel '{channel.name}'"
            )
            try:
                if isinstance(destination_config, HTTPDestinationConfig):
                    # Simulate HTTP POST/GET
                    logger.info(
                        f"Simulating HTTP {destination_config.method} to {destination_config.url} with message: {current_message}"
                    )
                    results.append(
                        {
                            "destination_type": "http",
                            "status": "sent",
                            "url": destination_config.url,
                        }
                    )
                elif isinstance(destination_config, TCPDestinationConfig):
                    # Simulate TCP send
                    logger.info(
                        f"Simulating TCP send to {destination_config.host}:{destination_config.port} with message: {current_message}"
                    )
                    results.append(
                        {
                            "destination_type": "tcp",
                            "status": "sent",
                            "host": destination_config.host,
                            "port": destination_config.port,
                        }
                    )
                else:
                    logger.warning(
                        f"Unknown destination type: {destination_config.type}"
                    )
                    results.append({"destination_type": "unknown", "status": "skipped"})
            except Exception as e:
                logger.error(
                    f"Error sending to destination {i} for channel '{channel.name}': {e}"
                )
                # Handle both Pydantic models and dictionaries
                if hasattr(destination_config, "type"):
                    destination_type = destination_config.type
                elif isinstance(destination_config, dict):
                    destination_type = destination_config.get("type", "unknown")
                else:
                    destination_type = "unknown"
                results.append(
                    {
                        "destination_type": destination_type,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return {
            "status": "success",
            "processed_message": current_message,
            "destination_results": results,
        }
