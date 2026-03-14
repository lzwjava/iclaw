# leanclaw (中文说明)

这是一个基于 Python 的交互式终端 REPL，用于在终端中与 GitHub Copilot 进行对话。

## 功能特性

- **多轮对话**：在终端中与 GitHub Copilot 进行持续对话。
- **原生工具调用**：当需要实时信息时，自动触发网页搜索。
- **可定制化**：在会话期间选择搜索提供商和模型。
- **GitHub OAuth 认证**：通过 GitHub 设备授权流程进行认证。
- **自动刷新**：在会话期间自动刷新 Copilot 令牌。
- **默认使用 GPT-5.2 模型**。

## 安装步骤

```bash
git clone https://github.com/lzwjava/leanclaw
cd leanclaw
pip install -e .
```

## 使用说明

1. **GitHub 认证（仅需一次）**：
   ```bash
   leanclaw-login
   ```
   这将启动 GitHub 设备授权流程，并将您的令牌保存到 `~/.config/leanclaw/config.json`。

2. **启动 REPL**：
   ```bash
   leanclaw
   ```

### 终端命令
- `/login`: 进行 GitHub 认证。
- `/model`: 查看并切换可用模型。
- `/search_provider`: 查看并切换网页搜索提供商（默认：DuckDuckGo）。
- `/copy`: 将最后一条回复复制到剪贴板。
- `/help`: 显示可用命令。
- `.exit`: 退出 REPL。

## 网页搜索（原生工具调用）
该代理配备了 `web_search` 工具。当您询问最近发生的事件或实时数据时，模型将自主调用该工具、获取内容并根据实时结果提供答案。

---

## 开发相关

### 运行测试
我们使用 `unittest` 和 `coverage` 进行测试。
```bash
python3 -m coverage run -m unittest discover tests
python3 -m coverage report -m
```

### 项目结构
```
leanclaw/
├── commands/     # 模块化 CLI 命令处理器
├── main.py       # 核心 REPL 循环和工具定义
├── github_api.py # GitHub/Copilot API 通信
├── web_search.py # DuckDuckGo 搜索和内容抓取逻辑
└── login.py      # OAuth 设备流程逻辑

tests/            # 单元测试
integration_tests/# 依赖网络的集成测试
```
