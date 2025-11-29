# Quick Start - Auto-Preview Frontend

## 🚀 Fastest Way to Start

### Option 1: One Command (Recommended)

```bash
./scripts/start-dev.sh
```

This will:
- ✅ Start backend API (port 8000)
- ✅ Start frontend (port 3000)
- ✅ Auto-open browser at http://localhost:3000

---

### Option 2: VS Code Launch

1. Press `F5` or go to Run & Debug
2. Select "Launch Full Stack"
3. Both servers start + browser opens

---

### Option 3: Manual

**Terminal 1 - Backend:**
```bash
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
```

Then open: http://localhost:3000

---

## 🌐 URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **WebSocket:** ws://localhost:8000/ws

---

## 📱 Auto-Preview Features

✅ **Auto-open browser** - Opens on start  
✅ **Hot reload** - Changes reflect immediately  
✅ **Port forwarding** - Works in remote/DevContainer  
✅ **Live Server** - VS Code extension support  

---

## 🎯 VS Code Extensions (Optional)

Install for best experience:
- **Live Server** - Right-click → Open with Live Server
- **Preview Server** - Next.js preview
- **Tailwind CSS IntelliSense** - CSS autocomplete

---

**Ready to go!** Run `./scripts/start-dev.sh` and the frontend will auto-open! 🚀
