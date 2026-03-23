from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Input,
    Static,
    ListView,
    ListItem,
    Button,
    RichLog,
)
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual import on
from v_agent.session import index as Session
from v_agent.storage.db import global_db
from v_agent.session import prompt as SessionPrompt
from v_agent.provider.provider import ProviderOptions
import time
import contextlib
import io


class SessionItem(ListItem):
    def __init__(self, session_info):
        super().__init__()
        self.session_info = session_info

    def compose(self) -> ComposeResult:
        yield Static(f"{self.session_info.title}")


class VAgentTUI(App):
    """V-Agent TUI for session management and interaction"""

    CSS = """
    Screen {
        background: #1a1a1a;
    }
    #sidebar {
        width: 30;
        border-right: solid green;
        height: 1fr;
    }
    #chat-container {
        height: 1fr;
    }
    #chat-log {
        height: 7fr;
        padding: 1;
        overflow-y: scroll;
    }
    #process-log {
        height: 3fr;
        border-top: dashed yellow;
        background: #000;
        color: #eee;
    }
    #input-container {
        height: auto;
        dock: bottom;
        border-top: solid white;
    }
    Input {
        margin: 1;
        border: double white;
    }
    .user-msg {
        color: yellow;
        margin: 1 0;
    }
    .ai-msg {
        color: magenta;
        margin: 1 0;
    }
    .system-msg {
        color: cyan;
        margin: 1 0;
        text-style: italic;
    }
    """

    BINDINGS = [
        ("n", "new_session", "New Session"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.current_session_id = None
        # Default provider for now
        self.provider = ProviderOptions(
            provider="alibaba",
            model="qwen3-max",
            api_key="sk-a156a06a92c44911b6f57715fb020783",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Button("New Session", id="btn-new-session", variant="primary")
                yield ListView(id="session-list")
            with Vertical(id="chat-container"):
                yield VerticalScroll(id="chat-log")
                yield RichLog(id="process-log", highlight=True, markup=True)
                with Vertical(id="input-container"):
                    yield Input(placeholder="Type your message...", id="user-input")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        session_list = self.query_one("#session-list", ListView)
        session_list.clear()
        sessions = Session.list()
        for s in sessions:
            session_list.append(SessionItem(s))

    @on(Button.Pressed, "#btn-new-session")
    def action_new_session(self) -> None:
        new_session = Session.create(
            {
                "directory": "tui_session",
                "title": f"Session {time.strftime('%H:%M:%S')}",
            }
        )
        self.refresh_sessions()
        # Automatically select the new session
        self.current_session_id = new_session.id
        self.load_session(new_session.id)

    @on(ListView.Selected, "#session-list")
    def on_session_selected(self, event: ListView.Selected) -> None:
        if event.item and isinstance(event.item, SessionItem):
            session_info = event.item.session_info
            self.current_session_id = session_info.id
            self.load_session(session_info.id)

    def load_session(self, session_id: str) -> None:
        self.current_session_id = session_id
        chat_log = self.query_one("#chat-log", VerticalScroll)
        chat_log.query("*").remove()

        try:
            messages = global_db.load_messages(session_id)
            for msg in messages:
                role = msg.info.role
                content = "".join([part.text for part in msg.parts])
                if role == "user":
                    chat_log.mount(
                        Static(
                            f"[bold yellow]You:[/bold yellow] {content}",
                            classes="user-msg",
                        )
                    )
                else:
                    chat_log.mount(
                        Static(
                            f"[bold magenta]AI ({msg.info.model}):[/bold magenta] {content}",
                            classes="ai-msg",
                        )
                    )
        except Exception as e:
            chat_log.mount(
                Static(f"[bold red]Error loading messages:[/bold red] {str(e)}")
            )

        chat_log.scroll_end(animate=False)
        self.query_one("#user-input").focus()

    @on(Input.Submitted, "#user-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        content = event.value.strip()
        if not content:
            return

        if not self.current_session_id:
            # Create a session if none selected
            self.action_new_session()

        chat_log = self.query_one("#chat-log", VerticalScroll)
        chat_log.mount(
            Static(f"[bold yellow]You:[/bold yellow] {content}", classes="user-msg")
        )
        self.query_one("#user-input", Input).value = ""
        chat_log.scroll_end()

        # Call prompt logic in worker thread
        if self.current_session_id:
            session_id = self.current_session_id
            self.run_worker(
                lambda: self.process_prompt_sync(session_id, content),
                thread=True,
            )

    def process_prompt_sync(self, session_id: str, content: str) -> None:
        chat_log = self.query_one("#chat-log", VerticalScroll)
        process_log = self.query_one("#process-log", RichLog)

        def update_ui_start():
            loading_msg = Static(
                "[italic cyan]AI is thinking...[/italic cyan]", id="loading-msg"
            )
            chat_log.mount(loading_msg)
            chat_log.scroll_end()
            process_log.clear()
            process_log.write("[bold yellow]Starting AI process...[/bold yellow]")
            return loading_msg

        loading_msg = self.call_from_thread(update_ui_start)

        try:
            # Ensure options is a dict if PromptInput expects it,
            # but LLM expects ProviderOptions. Let's pass it as is since it works.
            prompt_input = SessionPrompt.PromptInput(
                sessionID=session_id,
                options=self.provider,  # type: ignore
                content=content,
            )

            # Redirect stdout to RichLog
            class LogWriter(io.TextIOBase):
                def __init__(self, rich_log, app):
                    self.rich_log = rich_log
                    self.app = app
                    self.buffer = ""

                def write(self, string):
                    self.buffer += string
                    if "\n" in self.buffer:
                        lines = self.buffer.split("\n")
                        for line in lines[:-1]:
                            # Log writing must also be thread-safe
                            self.app.call_from_thread(self.rich_log.write, line)
                        self.buffer = lines[-1]
                    return len(string)

                def flush(self):
                    if self.buffer:
                        self.app.call_from_thread(self.rich_log.write, self.buffer)
                        self.buffer = ""

            with contextlib.redirect_stdout(LogWriter(process_log, self)):
                # Run the blocking prompt call
                SessionPrompt.prompt(prompt_input)

            def update_ui_end():
                loading_msg.remove()
                self.load_session(session_id)
                process_log.write("[bold green]AI process completed.[/bold green]")

            self.call_from_thread(update_ui_end)

        except Exception as e:

            def update_ui_error():
                if loading_msg:
                    loading_msg.remove()
                chat_log.mount(Static(f"[bold red]Error:[/bold red] {str(e)}"))
                chat_log.scroll_end()

            self.call_from_thread(update_ui_error)


def main():
    app = VAgentTUI()
    app.run()


if __name__ == "__main__":
    main()
