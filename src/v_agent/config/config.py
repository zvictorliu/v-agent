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

    type: str = "default"
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
    database_path: str = "database/v_agent.db"
    tools: list[str] = field(
        default_factory=lambda: ["get_weather", "calculate", "execute_command"]
    )
    _model: ModelConfig = field(default_factory=ModelConfig)
    models: dict[str, ModelConfig] = field(default_factory=dict)

    def __post_init__(self):
        load_dotenv()
        self._load_from_config_file()
        self._load_from_env()

    def _load_from_config_file(self):
        if self.config_file is None:
            self.config_file = Path("options/default.yaml")

        if not self.config_file.exists():
            return

        with open(self.config_file) as f:
            data = yaml.safe_load(f) or {}

        # 兼容新的 provider 键和旧的 model 键
        model_data = data.get("provider") or data.get("model")
        if model_data:
            if isinstance(model_data, list):
                for p_data in model_data:
                    if "models" in p_data and isinstance(p_data["models"], list):
                        provider_base = {
                            k: v for k, v in p_data.items() if k != "models"
                        }
                        for m_data in p_data["models"]:
                            model_cfg = ModelConfig()
                            # 继承 provider 级别的配置
                            for key, value in provider_base.items():
                                if hasattr(model_cfg, key):
                                    setattr(model_cfg, key, value)
                            # 覆盖 model 级别的配置
                            for key, value in m_data.items():
                                if hasattr(model_cfg, key):
                                    setattr(model_cfg, key, value)
                            self.models[model_cfg.type] = model_cfg
                    else:
                        model_cfg = ModelConfig()
                        for key, value in p_data.items():
                            if hasattr(model_cfg, key):
                                setattr(model_cfg, key, value)
                        self.models[model_cfg.type] = model_cfg

                if "default" in self.models:
                    self._model = self.models["default"]
                elif self.models:
                    self._model = list(self.models.values())[0]
            elif isinstance(model_data, dict):
                for key, value in model_data.items():
                    if hasattr(self._model, key):
                        setattr(self._model, key, value)
                self.models[self._model.type] = self._model

        # 加载数据库路径
        if "database" in data and "path" in data["database"]:
            self.database_path = data["database"]["path"]

        # 加载工具
        if "tools" in data:
            self.tools = data["tools"]

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
