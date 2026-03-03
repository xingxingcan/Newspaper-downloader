# -*- coding: utf-8 -*-
"""
配置管理器
负责保存和加载用户设置（如上次选择的保存目录、窗口大小等）
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """配置管理类，使用 JSON 文件存储用户偏好"""

    CONFIG_FILENAME = "newspaper_downloader_config.json"
    DEFAULT_SAVE_DIR = str(Path.home() / "Desktop")

    def __init__(self):
        self._config_path = self._get_config_path()
        self._config = self._load()

    def _get_config_path(self) -> Path:
        """获取配置文件路径（位于用户主目录或程序同级目录）"""
        # 优先使用程序所在目录，便于打包后 portable 使用
        app_dir = Path(__file__).resolve().parent.parent
        return app_dir / self.CONFIG_FILENAME

    def _load(self) -> dict:
        """从磁盘加载配置"""
        default = {
            "save_dir": self.DEFAULT_SAVE_DIR,
            "window_width": 900,
            "window_height": 700,
            "last_newspapers": [],
            "last_date": None,
        }
        try:
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default.update(loaded)
        except (json.JSONDecodeError, IOError):
            pass
        return default

    def _save(self) -> None:
        """将配置写入磁盘"""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    @property
    def save_dir(self) -> str:
        return self._config.get("save_dir", self.DEFAULT_SAVE_DIR)

    @save_dir.setter
    def save_dir(self, value: str) -> None:
        self._config["save_dir"] = value
        self._save()

    @property
    def window_size(self) -> tuple:
        return (
            self._config.get("window_width", 900),
            self._config.get("window_height", 700),
        )

    @window_size.setter
    def window_size(self, value: tuple) -> None:
        self._config["window_width"], self._config["window_height"] = value
        self._save()

    @property
    def last_newspapers(self) -> list:
        return self._config.get("last_newspapers", [])

    @last_newspapers.setter
    def last_newspapers(self, value: list) -> None:
        self._config["last_newspapers"] = value
        self._save()

    @property
    def last_date(self) -> str | None:
        return self._config.get("last_date")

    @last_date.setter
    def last_date(self, value: str | None) -> None:
        self._config["last_date"] = value
        self._save()
