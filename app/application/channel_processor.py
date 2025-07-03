# -*- coding: utf-8 -*-
# @Time  : 2025/07/03 17:30
# @Author: masonsxu
# @File  : channel_processor.py
# @Desc  : Application service for processing channel messages

import logging
from typing import Any
from sqlmodel import Session

from app.domain.models.channel import (
    ChannelModel,
    HTTPDestinationConfig,
    PythonScriptFilterConfig,
    PythonScriptTransformerConfig,
    TCPDestinationConfig,
)

logger = logging.getLogger(__name__)


class ChannelProcessor:
    def __init__(self):
        pass

    async def process_message(self, channel: ChannelModel, message: Any) -> dict:
        """Processes a message through the given channel's filters, transformers, and destinations."""
        logger.info(
            f"Processing message for channel '{channel.name}' (ID: {channel.id})"
        )
        current_message = message

        # --- Filters ---
        if channel.filters:
            for i, filter_config in enumerate(channel.filters):
                if isinstance(filter_config.__root__, PythonScriptFilterConfig):
                    script = filter_config.__root__.script
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
                if isinstance(
                    transformer_config.__root__, PythonScriptTransformerConfig
                ):
                    script = transformer_config.__root__.script
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
        for i, destination_config in enumerate(channel.destinations):
            logger.debug(
                f"Sending message to destination {i} for channel '{channel.name}'"
            )
            try:
                if isinstance(destination_config.__root__, HTTPDestinationConfig):
                    # Simulate HTTP POST/GET
                    logger.info(
                        f"Simulating HTTP {destination_config.__root__.method} to {destination_config.__root__.url} with message: {current_message}"
                    )
                    results.append(
                        {
                            "destination_type": "http",
                            "status": "sent",
                            "url": destination_config.__root__.url,
                        }
                    )
                elif isinstance(destination_config.__root__, TCPDestinationConfig):
                    # Simulate TCP send
                    logger.info(
                        f"Simulating TCP send to {destination_config.__root__.host}:{destination_config.__root__.port} with message: {current_message}"
                    )
                    results.append(
                        {
                            "destination_type": "tcp",
                            "status": "sent",
                            "host": destination_config.__root__.host,
                            "port": destination_config.__root__.port,
                        }
                    )
                else:
                    logger.warning(
                        f"Unknown destination type: {destination_config.__root__.type}"
                    )
                    results.append({"destination_type": "unknown", "status": "skipped"})
            except Exception as e:
                logger.error(
                    f"Error sending to destination {i} for channel '{channel.name}': {e}"
                )
                results.append(
                    {
                        "destination_type": destination_config.__root__.type,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return {
            "status": "success",
            "processed_message": current_message,
            "destination_results": results,
        }