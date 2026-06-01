# DevPilot AI

AI 自动化开发团队系统，当前处于 MVP Sprint 2：项目、模型、需求基础能力阶段。

## 基础设施连接

```env
DATABASE_URL=postgresql+psycopg://devpilot:devpilot123@192.168.194.2:5432/devpilot_ai
REDIS_URL=redis://192.168.194.2:6379/0
QDRANT_URL=http://192.168.194.2:6333
```

## 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell：

```powershell
Set-Location "e:\project\ai项目\DevPilot-AI\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

检查：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Swagger：

```text
http://localhost:8000/docs
```

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:3000
```

如果前端不在后端同机运行：

```bash
NEXT_PUBLIC_API_BASE_URL=http://后端IP:8000 npm run dev
```

## CLI

```bash
cd backend
python -m app.cli project list
python -m app.cli project create --name demo --local-path /path/to/project --language Python --framework FastAPI
```

如需连接非默认后端地址：

```bash
DEVPILOT_API_BASE_URL=http://后端IP:8000 python -m app.cli project list
```

## Docker 基础设施

```bash
cd docker
docker compose up -d
docker compose ps
```

检查：

```bash
docker exec -it devpilot-postgres psql -U devpilot -d devpilot_ai -c "SELECT version();"
docker exec -it devpilot-redis redis-cli ping
curl http://192.168.194.2:6333/readyz
```
