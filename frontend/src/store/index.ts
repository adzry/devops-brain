import { create } from 'zustand';
import type { Agent, Task, SystemHealth } from '@/lib/api';

interface AppState {
  // System
  health: SystemHealth | null;
  isConnected: boolean;
  
  // Agents
  agents: Agent[];
  selectedAgent: Agent | null;
  
  // Tasks
  tasks: Task[];
  selectedTask: Task | null;
  
  // UI
  sidebarOpen: boolean;
  modalOpen: string | null;
  
  // Actions
  setHealth: (health: SystemHealth | null) => void;
  setConnected: (connected: boolean) => void;
  setAgents: (agents: Agent[]) => void;
  selectAgent: (agent: Agent | null) => void;
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  selectTask: (task: Task | null) => void;
  toggleSidebar: () => void;
  openModal: (modal: string) => void;
  closeModal: () => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  health: null,
  isConnected: false,
  agents: [],
  selectedAgent: null,
  tasks: [],
  selectedTask: null,
  sidebarOpen: true,
  modalOpen: null,

  // Actions
  setHealth: (health) => set({ health }),
  setConnected: (isConnected) => set({ isConnected }),
  
  setAgents: (agents) => set({ agents }),
  selectAgent: (selectedAgent) => set({ selectedAgent }),
  
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, ...updates } : t
      ),
    })),
  selectTask: (selectedTask) => set({ selectedTask }),
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  openModal: (modal) => set({ modalOpen: modal }),
  closeModal: () => set({ modalOpen: null }),
}));
