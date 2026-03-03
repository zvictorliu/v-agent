import os
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ModelConfig:
    """模型配置"""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class Config:
    """分层配置加载器

    优先级（从低到高）: config.yaml < .env < cli
    """

    config_file: Optional[Path] = None
    _model: ModelConfig = field(default_factory=ModelConfig)

    def __post_init__(self):
        load_dotenv()
        self._load_from_config_file()
        self._load_from_env()

    def _load_from_config_file(self):
        if self.config_file is None:
            self.config_file = Path("config.yaml")

        if not self.config_file.exists():
            return

        with open(self.config_file) as f:
            data = yaml.safe_load(f) or {}

        if "model" in data:
            for key, value in data["model"].items():
                if hasattr(self._model, key):
                    setattr(self._model, key, value)

    def _load_from_env(self):
        env_mappings = {
            "MODEL_PROVIDER": "provider",
            "MODEL_NAME": "model",
            "OPENAI_API_KEY": "api_key",
            "OPENAI_base_url": "base_url",
            "MODEL_TEMPERATURE": "temperature",
            "MODEL_MAX_TOKENS": "max_tokens",
        }

        for env_key, attr_name in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                if attr_name in ("temperature", "max_tokens"):
                    value = float(value) if attr_name == "temperature" else int(value)
                setattr(self._model, attr_name, value)

    def update_from_cli(self, **kwargs):
        """从 CLI 参数更新配置（最高优先级）"""
        cli_mappings = {
            "provider": "provider",
            "model": "model",
            "api_key": "api_key",
            "base_url": "base_url",
            "temperature": "temperature",
            "max_tokens": "max_tokens",
        }

        for cli_arg, attr_name in cli_mappings.items():
            if cli_arg in kwargs and kwargs[cli_arg] is not None:
                value = kwargs[cli_arg]
                setattr(self._model, attr_name, value)

    @property
    def model(self) -> ModelConfig:
        return self._model


def get_config(config_file: Optional[Path] = None, **cli_kwargs) -> Config:
    """获取配置实例

    Args:
        config_file: 配置文件路径
        **cli_kwargs: CLI 参数

    Returns:
        Config: 配置对象
    """
    config = Config(config_file=config_file)
    config.update_from_cli(**cli_kwargs)
    return config
