# Frontend Link & Access Information

## 🚀 Frontend Access

### Local Development

**Frontend URL:**
```
http://localhost:3000
```

**Backend API URL:**
```
http://localhost:8000
```

**WebSocket URL:**
```
ws://localhost:8000/ws
```

---

## 📋 Quick Start

### Option 1: Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

Then access at: **http://localhost:3000**

---

### Option 2: Run with Docker Compose

Add frontend service to `docker-compose.yml`:

```yaml
frontend:
  build:
    context: ./frontend
  container_name: devops-brain-frontend
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8000
    - NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
  depends_on:
    - app
  networks:
    - devops-brain-network
```

Then:
```bash
docker-compose up frontend
```

Access at: **http://localhost:3000**

---

## 🌐 Production Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import to Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-api-domain.com`
   - `NEXT_PUBLIC_WS_URL=wss://your-api-domain.com/ws`
4. Deploy

**Vercel will provide:** `https://your-project.vercel.app`

---

### Docker Production

```bash
cd frontend
docker build -t devops-brain-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  -e NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws \
  devops-brain-frontend
```

---

## 📱 Frontend Pages

Once running, access these pages:

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/dashboard` | Main dashboard with stats |
| **Agents** | `/agents` | Agent management |
| **Tasks** | `/tasks` | Task execution & tracking |
| **Design** | `/design` | Design system showcase |
| **Settings** | `/settings` | Configuration |

---

## 🔗 Shareable Links

### For Local Development
```
http://localhost:3000
```

### For Production (if deployed)
```
https://your-frontend-domain.com
```

### For mgx.dev Review
If you want to share the frontend with mgx.dev:

1. **Deploy to Vercel** (easiest):
   - Push frontend to GitHub
   - Connect to Vercel
   - Get public URL: `https://devops-brain.vercel.app`

2. **Or use ngrok** for local sharing:
   ```bash
   ngrok http 3000
   # Share the ngrok URL
   ```

3. **Or deploy to your server**:
   - Build: `npm run build`
   - Serve: `npm start`
   - Share your server URL

---

## ⚙️ Environment Setup

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

For production:
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
```

---

## 🎯 Current Status

- ✅ Frontend code complete
- ✅ All pages implemented
- ✅ API integration ready
- ✅ WebSocket integration ready
- ⏳ Needs deployment for public access

---

## 📧 Share with mgx.dev

**If deployed:**
```
Frontend: https://your-frontend-url.com
Backend API: https://your-api-url.com
```

**If local only:**
Use ngrok or deploy to Vercel for sharing.

---

**Frontend is ready!** Just run `npm run dev` in the `frontend/` directory. 🚀
