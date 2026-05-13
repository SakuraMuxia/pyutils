"""
Configuration Loader
配置文件加载工具
"""
import os
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 全局配置
_config: dict = {}


def resolve_relative_path(config_path: str | None, relative_path: str) -> str:
    """将相对路径转换为绝对路径
    
    Args:
        config_path: 配置文件路径
        relative_path: 相对路径
        
    Returns:
        绝对路径
    """
    if not relative_path:
        return relative_path
    
    # 如果已经是绝对路径，直接返回
    if os.path.isabs(relative_path):
        return relative_path
    
    # 基于配置文件位置解析
    if config_path:
        config_dir = os.path.dirname(os.path.abspath(config_path))
        return os.path.normpath(os.path.join(config_dir, relative_path))
    
    # 基于当前工作目录
    return os.path.abspath(relative_path)


def load_config(config_path: str | None = None) -> dict:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    global _config
    
    if config_path is None:
        # 查找默认配置
        default_paths = [
            'config.yaml',
            'config.yml',
            os.path.join(os.path.dirname(__file__), '..', 'config.yaml'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'),
        ]
        
        for path in default_paths:
            path = os.path.abspath(path)
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path is None:
        logger.warning("No config file found, using defaults")
        return {}
    
    config_path = os.path.abspath(config_path)
    logger.info(f"Loading config: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f) or {}
    
    # 转换相对路径为绝对路径
    _resolve_paths(_config, config_path)
    
    return _config


def _resolve_paths(config: dict, config_path: str):
    """递归转换配置中的相对路径为绝对路径"""
    config_dir = os.path.dirname(os.path.abspath(config_path))
    
    # runtime 配置
    if 'runtime' in config:
        runtime = config['runtime']
        if 'fastwhisper_module_path' in runtime:
            runtime['fastwhisper_module_path'] = resolve_relative_path(config_path, runtime['fastwhisper_module_path'])
        if 'cuda_env_path' in runtime:
            runtime['cuda_env_path'] = resolve_relative_path(config_path, runtime['cuda_env_path'])
    
    # whisper 配置 - model_path
    if 'whisper' in config:
        whisper = config['whisper']
        if 'model_path' in whisper:
            whisper['model_path'] = resolve_relative_path(config_path, whisper['model_path'])


def get_config() -> dict:
    """
    获取已加载的配置
    
    Returns:
        配置字典
    """
    if not _config:
        load_config()
    return _config


def get(key: str, default: Any = None) -> Any:
    """
    获取配置项
    
    Args:
        key: 配置键 (支持点号，如 'whisper.device')
        default: 默认值
        
    Returns:
        配置值
    """
    config = get_config()
    
    # 支持点号分割的键
    keys = key.split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return default
        else:
            return default
    
    return value


def set_config(config: dict):
    """
    设置配置 (用于测试)
    
    Args:
        config: 配置字典
    """
    global _config
    _config = config