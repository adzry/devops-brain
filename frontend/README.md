# DevOps Brain Frontend

Modern, responsive dashboard for the DevOps Brain AI automation platform.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **State**: Zustand
- **Data Fetching**: SWR
- **Icons**: Lucide React
- **Charts**: Recharts

## Features

- 🎨 Beautiful dark-mode design system
- ⚡ Real-time updates via WebSocket
- 📊 Live dashboard with stats and metrics
- 🤖 Agent management and monitoring
- 📋 Task execution and tracking
- 🎨 Design system showcase
- ⚙️ Settings and configuration

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (dashboard)/        # Dashboard layout group
│   │   │   ├── dashboard/      # Main dashboard
│   │   │   ├── agents/         # Agents management
│   │   │   ├── tasks/          # Tasks list & execution
│   │   │   ├── design/         # Design system
│   │   │   └── settings/       # Settings page
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Root redirect
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── ui/                 # Base UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Badge.tsx
│   │   │   └── Modal.tsx
│   │   ├── layout/             # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   └── NewTaskModal.tsx    # Task creation modal
│   ├── hooks/
│   │   └── useWebSocket.ts     # WebSocket hook
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Utilities
│   └── store/
│       └── index.ts            # Zustand store
├── public/                     # Static assets
├── tailwind.config.ts          # Tailwind config
├── next.config.js              # Next.js config
└── package.json
```

## Pages

### Dashboard (`/dashboard`)
- System health overview
- Live stats (tasks, agents, success rate)
- Recent task activity
- Agent status monitoring
- Quick action buttons

### Agents (`/agents`)
- All 11 AI agents displayed
- Status indicators (online/busy/offline)
- Capabilities and success rates
- Execute actions directly

### Tasks (`/tasks`)
- Task list with filtering
- Status tracking (pending/running/completed/failed)
- Task details modal
- Real-time status updates

### Design (`/design`)
- Design tokens showcase
- Color palette
- Typography scale
- Spacing system
- Component library preview

### Settings (`/settings`)
- Instance configuration
- API key management
- Notification preferences
- Integration connections

## Design Tokens

The frontend uses a comprehensive design token system:

### Colors
- Primary: Indigo (#6366F1)
- Secondary: Rose (#F43F5E)
- Background: Slate-900 (#0F172A)
- Surface: Slate-800 (#1E293B)

### Typography
- Display: Cal Sans
- Body: Inter
- Mono: JetBrains Mono

### Effects
- Glass morphism backgrounds
- Glow shadows
- Smooth animations

## API Integration

The frontend connects to the DevOps Brain backend:

```typescript
import api from '@/lib/api';

// Fetch agents
const agents = await api.getAgents();

// Submit a task
const result = await api.submitTask('scan_vulnerabilities', {
  target: 'src/',
});

// Execute synchronously
const response = await api.executeTask('generate_tests', {
  file: 'api.py',
});
```

## WebSocket

Real-time updates are handled via WebSocket:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function Component() {
  const { isConnected, lastMessage, send } = useWebSocket();
  
  // Messages are automatically handled by the store
}
```

## Development

```bash
# Lint code
npm run lint

# Type check
npm run type-check

# Format code
npx prettier --write .
```

## Building

```bash
# Production build
npm run build

# The output is in .next/
```

## Deployment

The frontend can be deployed to:
- Vercel (recommended)
- Docker container
- Any Node.js hosting

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## License

MIT
