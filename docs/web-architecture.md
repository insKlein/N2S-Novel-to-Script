# N2S Web Architecture

N2S Web 是现有 CLI 的产品化入口，不替代命令行能力。

## 结构

```text
frontend/ Next.js 工作台
  -> HTTP API
backend/ FastAPI 服务
  -> 复用 scripts/n2s.py 命令函数
outputs/{剧本名}/
  -> analysis / planning / scripts / review / logs
```

## 后端

后端提供同步 API：

- `POST /api/convert`
- `POST /api/analyze`
- `POST /api/plan`
- `POST /api/write/{episode}`
- `POST /api/review/{episode}`
- `GET /api/projects/{title}`
- `GET /api/projects/{title}/episodes/{episode}`

初版不做账号、数据库和任务队列。所有产物仍写入 `outputs/{剧本名}/`。

## 前端

前端是单屏专业创作工作台：

- 左侧输入小说文本和项目设置。
- 中间预览 `ep<N>.yaml`。
- 右侧展示阶段状态和分析/规划/审核报告。

前端不直接读写本地文件，只通过 Python API 获取产物。

## 运行

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/uvicorn backend.app:app --reload --port 8000

cd frontend
npm install
npm run dev
```

如果前端与后端不在默认端口，可设置：

```bash
NEXT_PUBLIC_N2S_API_URL=http://127.0.0.1:8000
```
