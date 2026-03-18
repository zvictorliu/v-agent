import yaml
from pathlib import Path


class ProviderOptions:
    """大模型提供商选项"""

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        for key, value in kwargs.items():
            setattr(self, key, value)

    def load_from_file(self, file_path: str | Path):
        """从文件加载配置"""
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            return

        if "provider" in config:
            provider_config = config["provider"]
            for key, value in provider_config.items():
                setattr(self, key, value)

    @classmethod
    def from_file(cls, file_path: str | Path) -> "ProviderOptions":
        """从文件创建配置实例"""
        options = cls()
        options.load_from_file(file_path)
        return options
