/**
 * API Client for DevOps Brain Backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface Agent {
  name: string;
  type: string;
  description: string;
  status: 'online' | 'busy' | 'offline';
  capabilities: string[];
  priority: number;
  active_tasks: number;
}

export interface Task {
  id: string;
  action: string;
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  uptime: number;
  agents_online: number;
  tasks_pending: number;
  tasks_completed: number;
}

export interface DesignTokens {
  colors: Record<string, Record<string, string>>;
  typography: Record<string, Record<string, string>>;
  spacing: Record<string, string>;
  radii: Record<string, string>;
  shadows: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || 'Request failed',
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  // Health endpoints
  async getHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.request<SystemHealth>('/health');
  }

  async getLiveness(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/health/live');
  }

  async getReadiness(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/health/ready');
  }

  // Agent endpoints
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('/api/v1/agents');
  }

  async getAgent(name: string): Promise<ApiResponse<Agent>> {
    return this.request<Agent>(`/api/v1/agents/${name}`);
  }

  async executeAgentAction(
    agentName: string,
    action: string,
    payload: Record<string, unknown> = {}
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return this.request(`/api/v1/agents/${agentName}/execute`, {
      method: 'POST',
      body: JSON.stringify({ action, payload }),
    });
  }

  // Task endpoints
  async getTasks(limit: number = 50): Promise<ApiResponse<Task[]>> {
    return this.request<Task[]>(`/api/v1/tasks?limit=${limit}`);
  }

  async getTask(taskId: string): Promise<ApiResponse<Task>> {
    return this.request<Task>(`/api/v1/tasks/${taskId}`);
  }

  async submitTask(
    action: string,
    payload: Record<string, unknown> = {}
  ): Promise<ApiResponse<{ task_id: string }>> {
    return this.request('/api/v1/tasks/submit', {
      method: 'POST',
      body: JSON.stringify({ action, payload }),
    });
  }

  async executeTask(
    action: string,
    payload: Record<string, unknown> = {}
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return this.request('/api/v1/tasks/execute', {
      method: 'POST',
      body: JSON.stringify({ action, payload }),
    });
  }

  // Design endpoints
  async getDesignTokens(): Promise<ApiResponse<DesignTokens>> {
    return this.request<DesignTokens>('/api/v1/design/tokens');
  }

  async extractTokens(
    figmaFileKey: string
  ): Promise<ApiResponse<{ tokens: DesignTokens; css: string }>> {
    return this.request('/api/v1/design/tokens/extract', {
      method: 'POST',
      body: JSON.stringify({ figma_file_key: figmaFileKey }),
    });
  }

  async generateComponent(params: {
    component_type: string;
    component_name: string;
    framework?: string;
    styling?: string;
  }): Promise<ApiResponse<{ code: string; files: Array<{ path: string; content: string }> }>> {
    return this.request('/api/v1/design/components/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async auditDesign(targetPath: string = 'src'): Promise<
    ApiResponse<{
      issues: Array<{
        type: string;
        file: string;
        message: string;
        severity: string;
      }>;
      accessibility_score: number;
    }>
  > {
    return this.request('/api/v1/design/audit', {
      method: 'POST',
      body: JSON.stringify({ target_path: targetPath }),
    });
  }

  // Quick execute
  async execute(
    action: string,
    payload: Record<string, unknown> = {}
  ): Promise<ApiResponse<Record<string, unknown>>> {
    return this.request('/api/v1/execute', {
      method: 'POST',
      body: JSON.stringify({ action, payload }),
    });
  }
}

  // Workflow operations
  async getWorkflows(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/workflows', { method: 'GET' });
  }

  async getWorkflow(id: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/workflows/${id}`, { method: 'GET' });
  }

  async createWorkflow(workflow: any): Promise<ApiResponse<any>> {
    return this.request('/api/v1/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    });
  }

  async updateWorkflow(id: string, workflow: any): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(workflow),
    });
  }

  async deleteWorkflow(id: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/workflows/${id}`, { method: 'DELETE' });
  }

  async executeWorkflow(id: string, input?: any): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/workflows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify(input || {}),
    });
  }

export const api = new ApiClient();
export default api;
