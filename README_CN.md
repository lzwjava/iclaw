# iclaw（中文说明）

iclaw 是 [openclaw](https://github.com/lzwjava/openclaw) 的精简实现，专为企业受限环境设计。它是一个轻量级终端 REPL，通过 GitHub Copilot 提供 AI 编程辅助，适用于浏览器扩展、IDE 插件被封锁或受限的场景——无需任何额外组件，只需一个纯 Python CLI 即可运行。

*免责声明：所有 Copilot 测试均使用本人个人订阅和个人账户进行。*

![iclaw](./iclaw.jpg)

## 功能特性

- **多轮对话**：在终端中与 GitHub Copilot 进行持续对话。
- **原生工具调用**：模型可自主调用网页搜索、执行 Shell 命令和编辑文件。
- **多搜索引擎支持**：DuckDuckGo（默认）、Startpage、Bing 和 Tavily。
- **GitHub OAuth 认证**：通过 GitHub 设备授权流程进行认证。
- **自动刷新**：在会话期间自动刷新 Copilot 令牌。
- **默认使用 GPT-5.2 模型**。

## 安装步骤

```bash
git clone https://github.com/lzwjava/iclaw
cd iclaw
pip install -e .
```

## 使用说明

1. **启动 REPL**：
   ```bash
   iclaw
   ```

2. **GitHub 认证（首次运行时）**：
   ```
   /model_provider
   ```
   选择 `copilot`，然后按照 GitHub 设备授权流程操作。令牌将保存到 `~/.config/iclaw/config.json`。

### 终端命令
- `/model_provider`: 选择并认证模型提供商。
- `/model`: 查看并切换可用模型。
- `/search_provider`: 查看并切换网页搜索提供商（默认：DuckDuckGo）。
- `/copy`: 将最后一条回复复制到剪贴板。
- `/help`: 显示可用命令。
- `.exit`: 退出 REPL。

## 原生工具调用

模型可自主调用以下三个工具：

- **web_search**：使用选定的搜索引擎搜索网络上的最新信息。
- **exec**：执行 Shell 命令（30 秒超时）。
- **edit**：通过 unified diff 补丁创建或修改文件。

## 搜索引擎

在会话中使用 `/search_provider` 切换搜索引擎：

| 搜索引擎 | 需要 API Key | 说明 |
|----------|-------------|------|
| DuckDuckGo | 否 | 默认搜索引擎 |
| Startpage | 否 | 注重隐私 |
| Bing | 否 | 微软必应 |
| Tavily | 是（`TAVILY_API_KEY`） | AI 原生搜索 API |

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
iclaw/
├── commands/     # 模块化 CLI 命令处理器
├── tools/        # 工具实现（编辑）
├── main.py       # 核心 REPL 循环和工具定义
├── github_api.py # GitHub/Copilot API 通信
├── web_search.py # 搜索引擎和内容抓取逻辑
├── exec_tool.py  # Shell 命令执行工具
└── login.py      # OAuth 设备流程逻辑

tests/            # 单元测试
integration_tests/# 依赖网络的集成测试
```
