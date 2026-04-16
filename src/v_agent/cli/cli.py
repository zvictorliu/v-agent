import argparse
import asyncio
import sys
import time
import json
import shlex
from pathlib import Path
from typing import Optional, List
from colorama import Fore, Style as ColoramaStyle
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from ..config.config import Config, get_config
from ..session import index as SessionIndex
from ..session.info import SessionInfo
from ..session import prompt as SessionPrompt
from ..storage.db import global_db
from ..provider.provider import ProviderOptions
from ..tool.registry import ToolRegistry
from ..tool.tool import available_tools


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
        "-c",
        "--config",
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
        "--base-url",
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示推理内容（reasoning_content）",
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


def display_session_history(session_id: str):
    """显示会话历史消息"""
    try:
        messages = global_db.load_messages(session_id)
        if not messages:
            return

        for msg in messages:
            role = msg.info.role

            if role == "user":
                content = "".join([part.text for part in msg.parts])
                # 模拟用户输入的样式
                print(
                    f"\n{Fore.GREEN}{ColoramaStyle.BRIGHT}v-agent>{ColoramaStyle.RESET_ALL} {content}"
                )
            elif role == "system":
                content = "".join([part.text for part in msg.parts])
                print(f"\n{Fore.CYAN}System:{Fore.RESET} {content}")
            elif role == "tool":
                # 工具执行结果暂不展示，除非用户后续要求
                pass
            else:
                # AI 消息展示 logic
                printed_ai_prefix = False
                for part in msg.parts:
                    if part.type == "text":
                        if part.text.strip():
                            if not printed_ai_prefix:
                                print(f"\n{Fore.MAGENTA}AI:{Fore.RESET} {part.text}")
                                printed_ai_prefix = True
                            else:
                                # 如果已经打印过前缀，直接追加文本（或者换行）
                                print(f"{part.text}")
                    elif part.type == "tool-calls":
                        try:
                            calls = json.loads(part.text)
                            names = [c.get("name") for c in calls if c.get("name")]
                            for name in names:
                                # 用橙色(黄色)标识工具调用，用 ↳ 这个符号，不用 AI:
                                print(f"\n{Fore.YELLOW}↳ {name}{Fore.RESET}")
                        except Exception:
                            pass

        print()  # 最后的换行
    except Exception as e:
        print(f"{Fore.RED}Error loading history: {e}{Fore.RESET}")


def list_and_display_sessions() -> List[SessionInfo]:
    """列出并显示所有会话"""
    sessions = SessionIndex.list()
    if not sessions:
        print("No sessions found.")
        return []
    else:
        print("-" * 80)
        print(f"{'No.':<4} {'Title':<40} {'Created At':<20}")
        print("-" * 80)
        for i, s in enumerate(sessions, 1):
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.created_at))
            title = (s.title[:37] + "...") if len(s.title) > 40 else s.title
            print(f"{i:<4} {title:<40} {time_str:<20}")
        print("-" * 80)
        print("Use '/load <number>' to switch to a session.")
        return sessions


async def start_interactive_loop(config: Config, verbose: bool = False):
    """启动交互式循环

    Args:
        config: 配置对象
    """
    current_session: Optional[SessionInfo] = None
    last_listed_sessions: List[SessionInfo] = []

    tool_registry = ToolRegistry(tools=config.tools)

    model_cfg = config.model
    provider_options = ProviderOptions(
        provider=model_cfg.provider,
        api_key=model_cfg.api_key,
        model=model_cfg.model,
        base_url=model_cfg.base_url,
        temperature=model_cfg.temperature,
        max_tokens=model_cfg.max_tokens,
    )

    slash_commands = [
        "/help",
        "/exit",
        "/quit",
        "/settings",
        "/clear",
        "/new",
        "/load",
        "/sessions",
        "/tools",
        "/rename",
        "/delete",
        "/skills",
    ]
    completer = WordCompleter(slash_commands, ignore_case=True)

    history_file = Path.home() / ".v_agent_history"

    session = PromptSession(
        history=FileHistory(str(history_file)),
        completer=completer,
    )

    style = Style.from_dict(
        {
            "prompt": "ansigreen bold",
        }
    )

    print("Welcome to V-Agent! Type /help for assistance or /exit to quit.")

    while True:
        try:
            prompt_parts = [("class:prompt", "v-agent> ")]

            text = await session.prompt_async(prompt_parts, style=style)

            if not text.strip():
                continue

            if text.startswith("/"):
                parts = text.strip().split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if command in ["/exit", "/quit"]:
                    break
                elif command == "/help":
                    print("Available commands:")
                    print("  /help             - Show this help message")
                    print("  /new [title]      - Create a new session")
                    print("  /load <id|num>    - Load a session by ID or number")
                    print("  /sessions         - List all sessions")
                    print("  /rename <id|num> <title> - Rename a session")
                    print("  /delete <id|num>  - Delete a session")
                    print("  /tools            - List available tools")
                    print("  /skills           - List loaded skills")
                    print("  /settings         - Show current configuration")
                    print("  /clear            - Clear the screen")
                    print("  /exit, /quit      - Exit V-Agent")
                elif command == "/new":
                    session_input = {"title": args} if args else {}
                    current_session = SessionIndex.create(session_input)
                    print(
                        f"Created and switched to new session: {current_session.title}"
                    )
                elif command == "/load":
                    if not args:
                        print("Usage: /load <id|num>")
                        continue

                    target_session = None
                    if args.isdigit():
                        idx = int(args) - 1
                        if 0 <= idx < len(last_listed_sessions):
                            target_session = last_listed_sessions[idx]
                        else:
                            print(
                                f"Invalid session number: {args}. Please run /sessions first."
                            )
                            continue
                    else:
                        target_session = SessionIndex.get(args)

                    if target_session:
                        current_session = target_session
                        print(f"Loaded session: {current_session.title}")
                        display_session_history(current_session.id)
                    else:
                        print(f"Session not found: {args}")
                elif command == "/rename":
                    try:
                        rename_parts = shlex.split(args)
                    except ValueError as e:
                        print(f"Error parsing arguments: {e}")
                        continue

                    if len(rename_parts) < 2:
                        print("Usage: /rename <id|num> <new_title>")
                        continue

                    target_id_or_num = rename_parts[0]
                    new_title = " ".join(rename_parts[1:])

                    target_session_id = None
                    if target_id_or_num.isdigit():
                        idx = int(target_id_or_num) - 1
                        if 0 <= idx < len(last_listed_sessions):
                            target_session_id = last_listed_sessions[idx].id
                        else:
                            print(
                                f"Invalid session number: {target_id_or_num}. Please run /sessions first."
                            )
                            continue
                    else:
                        target_session_id = target_id_or_num

                    try:
                        SessionIndex.setTitle(target_session_id, new_title)
                        if current_session and current_session.id == target_session_id:
                            current_session.title = new_title
                        print(f"Session renamed to: {new_title}")
                        last_listed_sessions = list_and_display_sessions()
                    except Exception as e:
                        print(f"Error renaming session: {e}")

                elif command == "/delete":
                    if not args:
                        print("Usage: /delete <id|num>")
                        continue

                    target_session_id = None
                    if args.isdigit():
                        idx = int(args) - 1
                        if 0 <= idx < len(last_listed_sessions):
                            target_session_id = last_listed_sessions[idx].id
                        else:
                            print(
                                f"Invalid session number: {args}. Please run /sessions first."
                            )
                            continue
                    else:
                        target_session_id = args

                    try:
                        SessionIndex.remove(target_session_id)
                        if current_session and current_session.id == target_session_id:
                            current_session = None
                        print(f"Session deleted: {target_session_id}")
                        last_listed_sessions = list_and_display_sessions()
                    except Exception as e:
                        print(f"Error deleting session: {e}")

                elif command == "/sessions":
                    last_listed_sessions = list_and_display_sessions()
                elif command == "/clear":
                    print("\033[H\033[J", end="")
                elif command == "/settings":
                    print(f"Current Config: {config}")
                elif command == "/tools":
                    print("-" * 80)
                    print(f"{'Tool Name':<25} {'Description':<55}")
                    print("-" * 80)
                    tools = tool_registry.get_tools()
                    if not tools:
                        print("  No tools available.")
                    else:
                        for t in tools:
                            desc = t.description.strip().split("\n")[0]
                            if len(desc) > 52:
                                desc = desc[:52] + "..."
                            print(f"{t.name:<25} {desc:<55}")
                    print("-" * 80)
                elif command == "/skills":
                    print("-" * 80)
                    print(f"{'Skill Name':<25} {'Description':<55}")
                    print("-" * 80)
                    try:
                        from ..tool.skill import get_available_skills

                        skills = get_available_skills()
                        if not skills:
                            print("  No skills loaded.")
                        else:
                            for name, desc in skills.items():
                                desc_first_line = desc.strip().split("\n")[0]
                                if len(desc_first_line) > 52:
                                    desc_first_line = desc_first_line[:52] + "..."
                                print(f"{name:<25} {desc_first_line:<55}")
                    except ImportError:
                        print("  Skill module not available.")
                    print("-" * 80)
                else:
                    print(f"Unknown command: {command}")
            else:
                if not current_session:
                    current_session = SessionIndex.create({})

                prompt_input = SessionPrompt.PromptInput(
                    sessionID=current_session.id,
                    options=provider_options,
                    content=text,
                    tools=tool_registry.get_tools(),
                    verbose=verbose,
                )

                await SessionPrompt.prompt(prompt_input)
                print()

        except KeyboardInterrupt:
            continue
        except EOFError:
            break

    print("Goodbye!")


def main():
    args = parse_args()
    config: Config = get_config(args.config, **vars(args))

    asyncio.run(start_interactive_loop(config, verbose=args.verbose))


if __name__ == "__main__":
    main()
