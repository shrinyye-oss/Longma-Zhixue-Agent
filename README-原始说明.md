# 龙马智学 · Agent 复习实验室 V0.1

这是围绕第三届“信彩纷呈”创意编程大赛构建的**独立新原型**。它不修改既有《龙马寻踪 V1.0》游戏。目标是以最小可运行版本比较“校园互动游戏”与“课程智能复习工具”的参赛潜力。

> **资料边界：** 课程截图只提供了学习通 1.1–1.4、2.1–2.6 的章节名称。题库和知识讲解均由项目独立编写，明确标为**演示知识卡**，不是学习通课程原文或教师标准答案。

## 最快体验：0 安装、0 API 费用

1. 打开 `dist/龙马智学-离线可运行.html`（双击用浏览器打开）。
2. 点击 `RAG vs 微调` 等快速入口，或输入你的复习目标。
3. 查看检索到的知识卡，完成选择题；系统记录对错，并优先安排未答题或错题。
4. 在 `学习图谱` 中查看正确率、薄弱章节和下一轮复习建议。
5. 记录保存在本机浏览器 `localStorage`。换浏览器/隐私模式/清理数据可能丢失；可在“资料与说明”页面导出 JSON 备份。

这个离线模式是**规则驱动学习代理**，有可解释检索、状态更新、练习选择和闭环，但**不是大语言模型自主工具调用**。没有偷藏 API Key，也没有把本地规则冒充真正的 AI Agent。

## 可选：运行真实模型 Agent（需要 API Key）

Python 3.9+，仅使用 Python 标准库，无需 `pip install`。

在项目根目录通过终端设置环境变量，然后启动服务：

macOS / Linux：

```bash
export LLM_API_KEY='替换为自己的密钥'
export LLM_BASE_URL='https://你的模型服务商/v1'
export LLM_MODEL='服务商提供且支持tool-calling的模型名'
python agent_backend.py
```

Windows PowerShell：

```powershell
$env:LLM_API_KEY='替换为自己的密钥'
$env:LLM_BASE_URL='https://你的模型服务商/v1'
$env:LLM_MODEL='服务商提供且支持tool-calling的模型名'
python agent_backend.py
```

打开 `http://127.0.0.1:8765`，输入复习目标，点击学习路径下方出现的 `运行模型 Agent`。真实模型可以根据目标调用下列受控工具：

- `search_notes`：查询本地原创演示知识卡。
- `get_progress`：读取前端随请求传来的学习进度。
- `select_practice`：从结构化题库选题。

页面会显示**实际调用的工具名称和参数摘要**。如果模型没有调用任何工具，不会标记为已完成工具调用。请选用真正支持 OpenAI-compatible tool-calling 的服务商及模型；不同厂商格式仍可能有差异。

**密钥安全：** 密钥必须放在运行 Python 服务的环境变量里，不要放到 HTML、截图、GitHub 仓库里。默认仅绑定 `127.0.0.1`。第三方 API 调用可能产生费用，请自行设置服务商预算和限额。服务端不会保存你的学习记录；请求中的当前进度只为本次调用提供上下文。

## 项目结构

```text
龙马智学-Agent复习原型-V0.1/
├── dist/龙马智学-离线可运行.html    # 即开即用、无外部依赖
├── src/index.template.html         # UI 结构
├── src/style.css                   # 响应式样式
├── src/app.js                      # 本地检索/题目选择/进度管理
├── data/knowledge.json             # 10 章、20 道原创演示题
├── agent_backend.py                # 可选的真实模型工具调用服务
├── build.py                        # 将 CSS、JS、数据打包进单 HTML
├── tests/test_logic.py             # 数据与工具流程测试
├── docs/使用手册.md
├── docs/AI使用及原创性说明.md
└── README.md
```

重新构建：`python build.py`

运行测试：`python -m unittest discover -s tests -v`

## 技术架构及独创性

- 前端：不依赖框架，HTML/CSS/Vanilla JS；单 HTML 文件可离线运行。
- 内容：10个课程标题来自截图，20 道自编题目及相关知识卡来自项目作者，不依赖第三方课程正文。
- 检索：关键词加权与章节标签匹配；**不包含向量检索**，不应称为完整向量 RAG。
- 学习适配：依据章节答题次数、正确率和题目历史，优先推送未测或错误率较高的题目；不是训练好的预测模型。
- 模型 Agent：可选接入真实模型，通过多轮工具调用完成资料查询、进度读取及选题，不使用固定文本冒充模型输出。
- 安全：仅展示静态演示知识内容，模型配置由后端环境变量提供，适合本机演示。

## 开源参考

架构调研参考了 `langchain-ai/langgraphjs`（MIT）与 `microsoft/ai-agents-for-beginners`（MIT）两项 GitHub 开源项目；**本 V0.1 实现未复制它们的源码**，实际 Agent 工具循环由本项目独立编写。若后续直接复用其他仓库的代码或素材，应单独核查其许可证并保留归属说明。

- https://github.com/langchain-ai/langgraphjs
- https://github.com/microsoft/ai-agents-for-beginners

## 赛前实用判断

2026-11-16 截止前，建议保留《龙马寻踪 V1.0》作为稳定候选。本项目仅用于验证 Agent 方向，不建议在没有更完整真实课程资料、真实模型运行录像和校园特色设计的情况下，直接替换正式参赛成品。
