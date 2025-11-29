/**
 * Node Configuration Modal
 * 
 * Configure individual workflow nodes.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import type { WorkflowNode, NodeType } from './WorkflowBuilder';

interface NodeConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  node: WorkflowNode | null;
  onSave: (nodeId: string, config: Record<string, any>) => void;
}

export const NodeConfigModal: React.FC<NodeConfigModalProps> = ({
  isOpen,
  onClose,
  node,
  onSave,
}) => {
  const [config, setConfig] = useState<Record<string, any>>({});

  useEffect(() => {
    if (node) {
      setConfig(node.config);
    }
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onSave(node.id, config);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Configure ${node.name}`}
    >
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-300 mb-2 block">
            Node Name
          </label>
          <Input
            value={node.name}
            onChange={(e) => {
              // Update node name would be handled by parent
            }}
            placeholder="Node name"
          />
        </div>

        {node.type === 'task' && (
          <>
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                Action
              </label>
              <Input
                value={config.action || ''}
                onChange={(e) => setConfig({ ...config, action: e.target.value })}
                placeholder="e.g., scan_vulnerabilities"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                Agent (optional)
              </label>
              <Input
                value={config.agent || ''}
                onChange={(e) => setConfig({ ...config, agent: e.target.value })}
                placeholder="e.g., security_agent"
              />
            </div>
          </>
        )}

        {node.type === 'condition' && (
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              Condition Expression
            </label>
            <textarea
              value={config.condition || ''}
              onChange={(e) => setConfig({ ...config, condition: e.target.value })}
              className="w-full p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 font-mono text-sm"
              placeholder="result.status == 'success'"
              rows={3}
            />
          </div>
        )}

        {node.type === 'wait' && (
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              Wait Duration (seconds)
            </label>
            <Input
              type="number"
              value={config.duration || ''}
              onChange={(e) => setConfig({ ...config, duration: parseInt(e.target.value) || 0 })}
              placeholder="60"
            />
          </div>
        )}

        {node.type === 'approval' && (
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              Approval Timeout (minutes)
            </label>
            <Input
              type="number"
              value={config.timeout || ''}
              onChange={(e) => setConfig({ ...config, timeout: parseInt(e.target.value) || 60 })}
              placeholder="60"
            />
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-4">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save
          </Button>
        </div>
      </div>
    </Modal>
  );
};
