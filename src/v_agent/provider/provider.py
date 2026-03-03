class ProviderOptions:
    """大模型提供商选项"""
    def __init__(self, provider: str, api_key: str, model: str, **kwargs):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        for key, value in kwargs.items():
            setattr(self, key, value)