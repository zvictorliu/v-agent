# V-agent

个人 Agent 实现，基于 Python 编写，核心框架参考了 OpenCode 的设计思路

但在 LLM 抽象层上，借用了 Langchain，而不是 OpenCode 的 Vercel ai SDK

也因为此，整个 Agent Loop 的设计，尤其是在对 LLM 输出流的处理逻辑上和 OpenCode 有明显区别

## 使用方式

1. 安装依赖 `uv sync`

2. 在 `options` 中填写 api_key 信息，通过 `v_agent` 命令启动 cli 窗口

虽然也写了 TUI 模块，但还没有调教好，目前最适合用 CLI 来交互

