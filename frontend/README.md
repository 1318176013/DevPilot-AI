# DevPilot AI Frontend

## 本地启动

```bash
cd frontend
npm install
npm run dev
```

如果后端不在本机：

```bash
NEXT_PUBLIC_API_BASE_URL=http://后端地址:8000 npm run dev
```

Windows PowerShell:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```
