# N2S-Novel-to-Script

N2S 是一款 AI 辅助剧本创作工具，面向希望把小说改编成短剧/剧本初稿的作者。它参考 `novel-to-script-team` 的小说到剧本流程，只保留"小说文本 → 改编分析 → 分集规划 → YAML 剧本 → 审核报告"的核心链路。

## 核心能力

- 输入 3 个章节以上的小说文本。
- 支持粘贴文本，或导入 `.txt` / `.md` 小说文件。
- 自动生成结构化剧本初稿，输出为 YAML 文件。
- 保留 Agent / Skill / Reference 架构，便于后续继续扩展。
- 使用 OpenAI 兼容接口，可接入不同模型供应商。
- 支持分阶段运行，也支持一条命令完整转换。

## 快速开始

```bash
cd "/Users/apple/Documents/Novel2Script AI/七牛云/N2S-Novel-to-Script"
cp .env.example .env
```

编辑 `.env`：

```bash
N2S_API_KEY=your_api_key_here
N2S_BASE_URL=https://api.openai.com/v1
N2S_MODEL=your-model-name
```

完整转换：

```bash
python3 scripts/n2s.py convert --input examples/sample_novel.txt --title 示例剧本 --episodes 3
```

没有 API Key 时，可以用演示模式检查流程：

```bash
python3 scripts/n2s.py convert --input examples/sample_novel.txt --title 示例剧本 --episodes 3 --mock
```

## 分阶段命令

```bash
python3 scripts/n2s.py analyze --input examples/sample_novel.txt --title 示例剧本 --mock
python3 scripts/n2s.py plan --title 示例剧本 --episodes 3 --mock
python3 scripts/n2s.py write 1 --title 示例剧本 --mock
python3 scripts/n2s.py review 1 --title 示例剧本
python3 scripts/n2s.py final-check --title 示例剧本
```

## Web 工作台

Web 版本由 Python API 和 Next.js 前端组成。先安装依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd frontend && npm install
```

启动后端：

```bash
.venv/bin/uvicorn backend.app:app --reload --port 8000
```

启动前端：

```bash
cd frontend
npm run dev
```

打开 `http://localhost:3000`。默认使用演示模式，不需要 API Key；切换到真实模型模式前，请先配置 `.env`。

输入格式说明见 [docs/input-format.md](docs/input-format.md)。

也可以一键启动：

```bash
./scripts/start_web.sh
```

停止服务：

```bash
./scripts/stop_web.sh
```

## 输出目录

```text
outputs/{剧本名}/
├── .agent-state.json
├── analysis/
├── planning/
├── emotion-design/
├── scripts/
│   └── ep1.yaml
├── review/
├── knowledge/
└── logs/
```

核心产物是 `outputs/{剧本名}/scripts/ep<N>.yaml`。Schema 说明见 [docs/yaml-schema.md](docs/yaml-schema.md)。

如需校验手工修改后的 YAML，可安装可选依赖后运行：

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/validate_yaml.py outputs/示例剧本/scripts/ep1.yaml
```

## 架构说明

```text
用户命令
  -> Agent：谁负责
  -> Skill：怎么执行
  -> Reference：按什么标准判断
  -> Scripts：自动化辅助
  -> outputs：保存产物和状态
```

本项目保留小说到剧本所需的 10 个 Agent、12 个 Skill 和核心 Reference；不包含图片生成、视频生成、导演制作环节。

Web 架构说明见 [docs/web-architecture.md](docs/web-architecture.md)。

详见 [CLAUDE.md](./CLAUDE.md) 和 [zmq/novel-to-script-team-分析文档.md](./zmq/novel-to-script-team-分析文档.md)。
