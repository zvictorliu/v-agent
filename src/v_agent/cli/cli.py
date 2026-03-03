import argparse
from pathlib import Path
from typing import Optional
from ..config.config import Config, get_config

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        description="V-Agent 配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 配置文件
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=None,
    )

    # 模型相关参数
    model_group = parser.add_argument_group("模型配置")
    model_group.add_argument(
        "--provider",
        type=str,
        help="模型提供商 (e.g., openai, anthropic, qwen)",
        default=None,
    )
    model_group.add_argument(
        "--model",
        type=str,
        help="模型名称 (e.g., gpt-4o-mini, claude-3-haiku, qwen-turbo)",
        default=None,
    )
    model_group.add_argument(
        "--api-key",
        type=str,
        help="API Key",
        default=None,
    )
    model_group.add_argument(
        "--api-host",
        type=str,
        help="API 主机地址",
        default=None,
    )
    model_group.add_argument(
        "--temperature",
        type=float,
        help="采样温度 (0-2)",
        default=None,
    )
    model_group.add_argument(
        "--max-tokens",
        type=int,
        help="最大生成 token 数",
        default=None,
    )

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """解析命令行参数

    Args:
        args: 命令行参数列表 (默认从 sys.argv 解析)

    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = create_parser()
    return parser.parse_args(args)

def main():
    args = parse_args()
    config: Config = get_config(args.config, **vars(args))