'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import { Workflow, Play, Plus, Settings, Trash2, Edit } from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { WorkflowBuilder } from '@/components/workflow/WorkflowBuilder';
import { Modal } from '@/components/ui/Modal';
import api from '@/lib/api';

export default function WorkflowsPage() {
  const [view, setView] = useState<'list' | 'builder'>('list');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  
  // Fetch workflows
  const { data: workflowsData, mutate } = useSWR('/workflows', () => api.getWorkflows(), {
    refreshInterval: 5000,
  });
  const workflows = workflowsData?.data || [];

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      <Header
        title="Workflows"
        description="Create and manage automation workflows"
      />
      
      {view === 'list' ? (
        <div className="flex-1 overflow-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-100">Workflows</h2>
            <Button onClick={() => setView('builder')}>
              <Plus className="w-4 h-4 mr-2" />
              New Workflow
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflows.length === 0 ? (
              <Card className="col-span-full p-12 text-center">
                <Workflow className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                <CardTitle className="text-slate-300">No workflows yet</CardTitle>
                <CardDescription className="mt-2">
                  Create your first workflow to automate your DevOps tasks
                </CardDescription>
                <Button className="mt-4" onClick={() => setView('builder')}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Workflow
                </Button>
              </Card>
            ) : (
              workflows.map((workflow) => (
                <Card key={workflow.id} className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <CardTitle className="text-lg">{workflow.name}</CardTitle>
                      <CardDescription className="text-sm mt-1">
                        {workflow.description || 'No description'}
                      </CardDescription>
                    </div>
                    <Badge variant="success">Active</Badge>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-4">
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={async () => {
                        try {
                          await api.executeWorkflow(workflow.id);
                          alert('Workflow execution started!');
                        } catch (error: any) {
                          alert(`Failed to execute: ${error.message}`);
                        }
                      }}
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Run
                    </Button>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={() => {
                        setSelectedWorkflowId(workflow.id);
                        setView('builder');
                      }}
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      Edit
                    </Button>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={async () => {
                        if (confirm('Delete this workflow?')) {
                          try {
                            await api.deleteWorkflow(workflow.id);
                            mutate();
                          } catch (error: any) {
                            alert(`Failed to delete: ${error.message}`);
                          }
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden">
          <WorkflowBuilder />
          <div className="p-4 border-t border-slate-700 bg-slate-800/50">
            <Button variant="ghost" onClick={() => setView('list')}>
              ← Back to List
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
