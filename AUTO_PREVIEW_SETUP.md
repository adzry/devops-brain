# Auto-Preview Frontend Setup

**Status:** ✅ Configured

---

## 🚀 Quick Start

### Option 1: Use Script (Easiest)

```bash
./scripts/start-frontend.sh
```

This will:
- ✅ Install dependencies if needed
- ✅ Start Next.js dev server
- ✅ Auto-open browser at http://localhost:3000

---

### Option 2: Manual Start

```bash
cd frontend
npm install  # First time only
npm run dev:open
```

---

## 🔧 VS Code Extensions (Recommended)

Install these extensions for best experience:

1. **Live Server** (`ritwickdey.liveserver`)
   - Right-click HTML → "Open with Live Server"
   - Auto-reload on file changes

2. **Preview Server** (`bradlc.vscode-tailwindcss`)
   - Preview Next.js pages
   - Tailwind CSS IntelliSense

3. **ES7+ React/Redux/React-Native snippets**
   - Code snippets for React

---

## 🌐 Port Forwarding

If using remote development (DevContainer/SSH):

**Ports automatically forwarded:**
- `3000` → Frontend (Next.js)
- `8000` → Backend API (FastAPI)
- `5432` → PostgreSQL
- `6379` → Redis
- `9090` → Prometheus

**Auto-open configured:**
- Port 3000 opens browser automatically
- Port 9090 opens Prometheus automatically

---

## 📱 Access URLs

### Local Development
```
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

### Remote/DevContainer
```
Frontend: http://localhost:3000 (forwarded)
Backend:  http://localhost:8000 (forwarded)
```

---

## ⚙️ Configuration Files

### VS Code Settings
- `.vscode/settings.json` - Live Server config
- `frontend/.vscode/settings.json` - Frontend-specific

### DevContainer
- `.devcontainer/devcontainer.json` - Auto-port forwarding

### Scripts
- `scripts/start-frontend.sh` - Auto-start script

---

## 🎯 Features Enabled

✅ **Auto-open browser** - Opens on dev server start  
✅ **Hot reload** - Changes reflect immediately  
✅ **Port forwarding** - Works in remote environments  
✅ **Live Server** - VS Code extension support  
✅ **Preview Server** - Next.js preview support  

---

## 🚀 Start Now

```bash
cd frontend
npm run dev:open
```

**Or use the script:**
```bash
./scripts/start-frontend.sh
```

---

**Frontend will auto-open at http://localhost:3000** 🎉
