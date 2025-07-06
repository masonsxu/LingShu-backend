"""Loguru日志配置模块"""

import os
import sys
from pathlib import Path

from loguru import logger

# 移除默认的日志处理器
logger.remove()


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    log_rotation: str = "100 MB",
    log_retention: str = "30 days",
    enable_console: bool = True,
    enable_file: bool = True,
    format_string: str | None = None,
) -> None:
    """配置loguru日志

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，默认为logs/lingshu.log
        log_rotation: 日志轮转策略，默认100MB
        log_retention: 日志保留时间，默认30天
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        format_string: 自定义日志格式
    """

    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 控制台输出
    if enable_console:
        logger.add(
            sys.stdout,
            level=log_level,
            format=format_string,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # 文件输出
    if enable_file:
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "lingshu.log"

        logger.add(
            log_file,
            level=log_level,
            format=format_string,
            rotation=log_rotation,
            retention=log_retention,
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )


def setup_development_logging():
    """开发环境日志配置"""
    setup_logging(
        log_level="DEBUG",
        enable_console=True,
        enable_file=True,
        format_string=(
            "<green>{time:HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> | "
            "<magenta>{extra}</magenta>"
        ),
    )


def setup_production_logging():
    """生产环境日志配置"""
    setup_logging(
        log_level="INFO",
        enable_console=False,
        enable_file=True,
        log_rotation="500 MB",
        log_retention="90 days",
        format_string=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level} | "
            "{name}:{function}:{line} | "
            "{message} | "
            "{extra}"
        ),
    )


def setup_test_logging():
    """测试环境日志配置"""
    setup_logging(
        log_level="WARNING",
        enable_console=True,
        enable_file=False,
        format_string="<level>{level}</level> | {message}",
    )


def get_logger(name: str):
    """获取logger实例

    Args:
        name: logger名称，通常使用__name__

    Returns:
        配置好的logger实例
    """
    return logger.bind(module=name)


def log_function_call(func):
    """函数调用日志装饰器"""

    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"
        logger.debug(f"调用函数: {func_name}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数完成: {func_name}")
            return result
        except Exception as e:
            logger.error(f"函数异常: {func_name} - {e}")
            raise

    return wrapper


def log_async_function_call(func):
    """异步函数调用日志装饰器"""

    async def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__qualname__}"
        logger.debug(f"调用异步函数: {func_name}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"异步函数完成: {func_name}")
            return result
        except Exception as e:
            logger.error(f"异步函数异常: {func_name} - {e}")
            raise

    return wrapper


# 根据环境变量自动配置日志
def auto_setup_logging():
    """根据环境变量自动配置日志"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        setup_production_logging()
        logger.info("日志系统已配置为生产环境模式")
    elif env == "test":
        setup_test_logging()
        logger.info("日志系统已配置为测试环境模式")
    else:
        setup_development_logging()
        logger.info("日志系统已配置为开发环境模式")


# 导出主要的logger实例
__all__ = [
    "logger",
    "setup_logging",
    "setup_development_logging",
    "setup_production_logging",
    "setup_test_logging",
    "get_logger",
    "log_function_call",
    "log_async_function_call",
    "auto_setup_logging",
]
