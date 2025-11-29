/**
 * Visual Workflow Builder
 * 
 * Drag-and-drop workflow builder integrated with DevOps Brain workflow engine.
 * Rebuilds workflow-builder functionality inside DevOps Brain.
 */

'use client';

import React, { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Square,
  GitBranch,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Trash2,
  Save,
  Download,
  Upload,
  Settings,
  Zap,
} from 'lucide-react';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import { NodeConfigModal } from './NodeConfigModal';

// Workflow node types
export type NodeType = 
  | 'task' 
  | 'condition' 
  | 'parallel' 
  | 'wait' 
  | 'transform' 
  | 'notify'
  | 'approval'
  | 'checkpoint'
  | 'retry';

export interface WorkflowNode {
  id: string;
  type: NodeType;
  name: string;
  config: Record<string, any>;
  position: { x: number; y: number };
  connections: string[]; // IDs of connected nodes
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  condition?: string;
}

export interface WorkflowDefinition {
  id?: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  schedule?: string; // Cron expression
  webhook?: string;
  metadata?: Record<string, any>;
}

const NODE_TYPES: Record<NodeType, { label: string; icon: React.ComponentType; color: string }> = {
  task: { label: 'Task', icon: Zap, color: 'bg-blue-500' },
  condition: { label: 'Condition', icon: GitBranch, color: 'bg-yellow-500' },
  parallel: { label: 'Parallel', icon: Square, color: 'bg-purple-500' },
  wait: { label: 'Wait', icon: Clock, color: 'bg-orange-500' },
  transform: { label: 'Transform', icon: Settings, color: 'bg-green-500' },
  notify: { label: 'Notify', icon: AlertCircle, color: 'bg-pink-500' },
  approval: { label: 'Approval', icon: CheckCircle, color: 'bg-indigo-500' },
  checkpoint: { label: 'Checkpoint', icon: Save, color: 'bg-teal-500' },
  retry: { label: 'Retry', icon: XCircle, color: 'bg-red-500' },
};

export const WorkflowBuilder: React.FC = () => {
  const [workflow, setWorkflow] = useState<WorkflowDefinition>({
    name: 'New Workflow',
    description: '',
    nodes: [],
    edges: [],
  });
  
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isNodeConfigOpen, setIsNodeConfigOpen] = useState(false);
  const [configuringNode, setConfiguringNode] = useState<WorkflowNode | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Add new node
  const addNode = useCallback((type: NodeType, position: { x: number; y: number }) => {
    const newNode: WorkflowNode = {
      id: `node_${Date.now()}`,
      type,
      name: `${NODE_TYPES[type].label} ${workflow.nodes.length + 1}`,
      config: {},
      position,
      connections: [],
    };
    
    setWorkflow(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode],
    }));
  }, [workflow.nodes.length]);

  // Delete node
  const deleteNode = useCallback((nodeId: string) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.filter(n => n.id !== nodeId),
      edges: prev.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
    }));
    if (selectedNode === nodeId) {
      setSelectedNode(null);
    }
  }, [selectedNode]);

  // Connect nodes
  const connectNodes = useCallback((sourceId: string, targetId: string) => {
    setWorkflow(prev => {
      const edgeExists = prev.edges.some(
        e => e.source === sourceId && e.target === targetId
      );
      
      if (edgeExists) return prev;
      
      return {
        ...prev,
        edges: [...prev.edges, {
          id: `edge_${Date.now()}`,
          source: sourceId,
          target: targetId,
        }],
      };
    });
  }, []);

  // Update node position
  const updateNodePosition = useCallback((nodeId: string, position: { x: number; y: number }) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.map(n => 
        n.id === nodeId ? { ...n, position } : n
      ),
    }));
  }, []);

  // Update node config
  const updateNodeConfig = useCallback((nodeId: string, config: Record<string, any>) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.map(n =>
        n.id === nodeId ? { ...n, config: { ...n.config, ...config } } : n
      ),
    }));
  }, []);

  // Save workflow
  const saveWorkflow = async () => {
    setIsSaving(true);
    try {
      // Convert to DAG format for backend
      const workflowData = {
        name: workflow.name,
        description: workflow.description,
        nodes: workflow.nodes.map(n => ({
          id: n.id,
          type: n.type,
          name: n.name,
          action: n.config.action || '',
          agent: n.config.agent || null,
          payload: n.config.payload || {},
          condition: n.config.condition || null,
          timeout: n.config.timeout || 300,
          retry_count: n.config.retry_count || 0,
        })),
        edges: workflow.edges.map(e => ({
          source: e.source,
          target: e.target,
          condition: e.condition || null,
        })),
        metadata: {
          schedule: workflow.schedule,
          webhook: workflow.webhook,
          ...workflow.metadata,
        },
      };

      // Call workflow API
      const response = await api.createWorkflow(workflowData);
      
      if (response.status === 201 || response.status === 200) {
        alert('Workflow saved successfully!');
        setWorkflow(prev => ({ ...prev, id: response.data?.id }));
      } else {
        throw new Error(response.error || 'Failed to save workflow');
      }
    } catch (error: any) {
      console.error('Failed to save workflow:', error);
      alert(`Failed to save workflow: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Load workflow template
  const loadTemplate = useCallback((templateName: string) => {
    // Load from workflow templates
    const templates: Record<string, WorkflowDefinition> = {
      ci: {
        name: 'CI Pipeline',
        description: 'Continuous Integration workflow',
        nodes: [
          { id: 'n1', type: 'task', name: 'Lint', config: { action: 'lint' }, position: { x: 100, y: 100 }, connections: [] },
          { id: 'n2', type: 'task', name: 'Test', config: { action: 'test' }, position: { x: 300, y: 100 }, connections: [] },
          { id: 'n3', type: 'task', name: 'Build', config: { action: 'build' }, position: { x: 500, y: 100 }, connections: [] },
        ],
        edges: [
          { id: 'e1', source: 'n1', target: 'n2' },
          { id: 'e2', source: 'n2', target: 'n3' },
        ],
      },
      deploy: {
        name: 'Deployment Pipeline',
        description: 'Deployment workflow',
        nodes: [
          { id: 'n1', type: 'task', name: 'Build', config: {}, position: { x: 100, y: 100 }, connections: [] },
          { id: 'n2', type: 'approval', name: 'Approve', config: {}, position: { x: 300, y: 100 }, connections: [] },
          { id: 'n3', type: 'task', name: 'Deploy', config: {}, position: { x: 500, y: 100 }, connections: [] },
        ],
        edges: [
          { id: 'e1', source: 'n1', target: 'n2' },
          { id: 'e2', source: 'n2', target: 'n3' },
        ],
      },
    };

    const template = templates[templateName];
    if (template) {
      setWorkflow(template);
    }
  }, []);

  // Handle canvas click
  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const position = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
      // Add default task node on click
      addNode('task', position);
    }
  }, [addNode]);

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800/50">
        <div className="flex items-center gap-4">
          <Input
            value={workflow.name}
            onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Workflow Name"
            className="w-64"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => loadTemplate('ci')}
          >
            Load CI Template
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => loadTemplate('deploy')}
          >
            Load Deploy Template
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsConfigModalOpen(true)}
          >
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={saveWorkflow}
            disabled={isSaving}
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
          <Button
            size="sm"
            onClick={async () => {
              if (!workflow.id) {
                alert('Please save the workflow first');
                return;
              }
              try {
                const response = await api.executeWorkflow(workflow.id);
                if (response.status === 200) {
                  alert('Workflow execution started!');
                }
              } catch (error: any) {
                alert(`Failed to execute workflow: ${error.message}`);
              }
            }}
            disabled={!workflow.id}
          >
            <Play className="w-4 h-4 mr-2" />
            Run
          </Button>
        </div>
      </div>

      {/* Node Palette */}
      <div className="flex items-center gap-2 p-2 border-b border-slate-700 bg-slate-800/30 overflow-x-auto">
        {Object.entries(NODE_TYPES).map(([type, { label, icon: Icon, color }]) => (
          <Button
            key={type}
            variant="ghost"
            size="sm"
            onClick={() => {
              const rect = canvasRef.current?.getBoundingClientRect();
              if (rect) {
                addNode(type as NodeType, {
                  x: rect.width / 2,
                  y: rect.height / 2,
                });
              }
            }}
            className="flex items-center gap-2"
          >
            <Icon className={cn('w-4 h-4', color)} />
            <span>{label}</span>
          </Button>
        ))}
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        className="flex-1 relative overflow-auto bg-slate-900/50"
        onClick={handleCanvasClick}
        style={{
          backgroundImage: 'radial-gradient(circle, #334155 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      >
        {/* Render edges */}
        <svg className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%' }}>
          {workflow.edges.map(edge => {
            const sourceNode = workflow.nodes.find(n => n.id === edge.source);
            const targetNode = workflow.nodes.find(n => n.id === edge.target);
            
            if (!sourceNode || !targetNode) return null;
            
            const x1 = sourceNode.position.x + 100;
            const y1 = sourceNode.position.y + 40;
            const x2 = targetNode.position.x;
            const y2 = targetNode.position.y + 40;
            
            return (
              <line
                key={edge.id}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#6366F1"
                strokeWidth="2"
                markerEnd="url(#arrowhead)"
              />
            );
          })}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#6366F1" />
            </marker>
          </defs>
        </svg>

        {/* Render nodes */}
        <AnimatePresence>
          {workflow.nodes.map(node => {
            const NodeIcon = NODE_TYPES[node.type].icon;
            const nodeColor = NODE_TYPES[node.type].color;
            
            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className={cn(
                  'absolute cursor-move',
                  selectedNode === node.id && 'ring-2 ring-primary-500'
                )}
                style={{
                  left: node.position.x,
                  top: node.position.y,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNode(node.id);
                  setConfiguringNode(node);
                  setIsNodeConfigOpen(true);
                }}
                onDragStart={(e) => {
                  const rect = (e.target as HTMLElement).getBoundingClientRect();
                  setDragOffset({
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top,
                  });
                }}
                onDrag={(e) => {
                  if (canvasRef.current) {
                    const rect = canvasRef.current.getBoundingClientRect();
                    updateNodePosition(node.id, {
                      x: e.clientX - rect.left - (dragOffset?.x || 0),
                      y: e.clientY - rect.top - (dragOffset?.y || 0),
                    });
                  }
                }}
                draggable
              >
                <Card className="w-48 p-3 bg-slate-800 border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-full', nodeColor)} />
                      <span className="text-sm font-medium text-slate-200">
                        {node.name}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNode(node.id);
                      }}
                      className="h-6 w-6 p-0"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <NodeIcon className="w-3 h-3" />
                    <span>{NODE_TYPES[node.type].label}</span>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Node Configuration Modal */}
      <NodeConfigModal
        isOpen={isNodeConfigOpen}
        onClose={() => {
          setIsNodeConfigOpen(false);
          setConfiguringNode(null);
        }}
        node={configuringNode}
        onSave={updateNodeConfig}
      />

      {/* Workflow Settings Modal */}
      <Modal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        title="Workflow Settings"
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-300">Schedule (Cron)</label>
            <Input
              value={workflow.schedule || ''}
              onChange={(e) => setWorkflow(prev => ({ ...prev, schedule: e.target.value }))}
              placeholder="0 2 * * *"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-300">Webhook URL</label>
            <Input
              value={workflow.webhook || ''}
              onChange={(e) => setWorkflow(prev => ({ ...prev, webhook: e.target.value }))}
              placeholder="https://..."
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-300">Description</label>
            <textarea
              value={workflow.description}
              onChange={(e) => setWorkflow(prev => ({ ...prev, description: e.target.value }))}
              className="w-full p-2 bg-slate-800 border border-slate-700 rounded text-slate-200"
              rows={3}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
