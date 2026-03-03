# -*- coding: utf-8 -*-
"""
配置管理模块
负责应用配置的加载、保存和报纸源的定义
"""

from .config_manager import ConfigManager
from .newspaper_sources import NEWSPAPER_SOURCES

__all__ = ["ConfigManager", "NEWSPAPER_SOURCES"]
