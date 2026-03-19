from .llm import LLM
from colorama import Fore

class SessionProcessor:
    def __init__(self, sessionID, options):
        self.sessionID = sessionID
        self.client = LLM(options)

    def process(self, input: LLM.StreamInput):
        """处理会话"""

        current_type = None
        response_stream = self.client.stream(input)
        for value in response_stream:
            new_type = value["type"]
            if new_type != current_type:
                if current_type is not None:
                    print()  # 切换类型时换行
                if new_type == "reasoning":
                    print(Fore.YELLOW + "[Reasoning] " + Fore.RESET, end="", flush=True)
                elif new_type == "message":
                    print(Fore.GREEN + "[Message] " + Fore.RESET, end="", flush=True)
                elif new_type == "tool_calling":
                    print(
                        Fore.BLUE + "[Tool Calling] " + Fore.RESET, end="", flush=True
                    )
                current_type = new_type

            if new_type == "reasoning":
                print(Fore.YELLOW + value["content"] + Fore.RESET, end="", flush=True)
            elif new_type == "message":
                print(Fore.GREEN + value["content"] + Fore.RESET, end="", flush=True)
            elif new_type == "tool_calling":
                print(
                    Fore.BLUE
                    + f"Tool: {value['name']}, Args: {value['args']}"
                    + Fore.RESET,
                    end="",
                    flush=True,
                )
        print()  # 结束时换行
        return "stop"
