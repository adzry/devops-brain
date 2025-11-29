"""
Agent Load Balancer

Distributes tasks across multiple agent instances for better performance.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class LoadBalancingStrategy:
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"


@dataclass
class AgentInstance:
    """Represents an agent instance for load balancing."""
    name: str
    instance_id: str
    weight: int = 1
    active_tasks: int = 0
    total_tasks: int = 0
    last_used: Optional[datetime] = None
    health_score: float = 1.0  # 0.0 to 1.0
    response_time_ms: float = 0.0


class LoadBalancer:
    """
    Load balancer for distributing tasks across agent instances.
    
    Features:
    - Multiple balancing strategies
    - Health-aware routing
    - Weighted distribution
    - Performance tracking
    """
    
    def __init__(self, strategy: str = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self._agents: dict[str, list[AgentInstance]] = {}  # agent_name -> instances
        self._round_robin_index: dict[str, int] = {}  # agent_name -> index
        self._lock = asyncio.Lock()
    
    def register_instance(
        self,
        agent_name: str,
        instance_id: str,
        weight: int = 1,
    ) -> None:
        """Register an agent instance."""
        async def _register():
            async with self._lock:
                if agent_name not in self._agents:
                    self._agents[agent_name] = []
                    self._round_robin_index[agent_name] = 0
                
                instance = AgentInstance(
                    name=agent_name,
                    instance_id=instance_id,
                    weight=weight,
                )
                
                self._agents[agent_name].append(instance)
                logger.info(f"Registered agent instance: {agent_name}/{instance_id}")
        
        asyncio.create_task(_register())
    
    def unregister_instance(self, agent_name: str, instance_id: str) -> None:
        """Unregister an agent instance."""
        if agent_name in self._agents:
            self._agents[agent_name] = [
                inst for inst in self._agents[agent_name]
                if inst.instance_id != instance_id
            ]
    
    async def select_instance(self, agent_name: str) -> Optional[str]:
        """
        Select an agent instance using load balancing strategy.
        
        Args:
            agent_name: Name of the agent type
            
        Returns:
            Instance ID or None if no instances available
        """
        async with self._lock:
            instances = self._agents.get(agent_name, [])
            
            if not instances:
                return None
            
            # Filter healthy instances
            healthy_instances = [
                inst for inst in instances
                if inst.health_score > 0.5
            ]
            
            if not healthy_instances:
                # Fallback to all instances if none are healthy
                healthy_instances = instances
            
            # Select based on strategy
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected = self._round_robin(agent_name, healthy_instances)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected = self._least_connections(healthy_instances)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                selected = self._random(healthy_instances)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED:
                selected = self._weighted(healthy_instances)
            else:
                selected = healthy_instances[0]
            
            if selected:
                selected.active_tasks += 1
                selected.total_tasks += 1
                selected.last_used = datetime.utcnow()
                return selected.instance_id
            
            return None
    
    async def release_instance(self, agent_name: str, instance_id: str) -> None:
        """Release an instance (decrement active tasks)."""
        async with self._lock:
            instances = self._agents.get(agent_name, [])
            for inst in instances:
                if inst.instance_id == instance_id:
                    inst.active_tasks = max(0, inst.active_tasks - 1)
                    break
    
    def _round_robin(self, agent_name: str, instances: list[AgentInstance]) -> Optional[AgentInstance]:
        """Round-robin selection."""
        if not instances:
            return None
        
        index = self._round_robin_index.get(agent_name, 0)
        selected = instances[index % len(instances)]
        self._round_robin_index[agent_name] = (index + 1) % len(instances)
        return selected
    
    def _least_connections(self, instances: list[AgentInstance]) -> Optional[AgentInstance]:
        """Select instance with least active connections."""
        if not instances:
            return None
        
        return min(instances, key=lambda inst: inst.active_tasks)
    
    def _random(self, instances: list[AgentInstance]) -> Optional[AgentInstance]:
        """Random selection."""
        if not instances:
            return None
        
        return random.choice(instances)
    
    def _weighted(self, instances: list[AgentInstance]) -> Optional[AgentInstance]:
        """Weighted random selection."""
        if not instances:
            return None
        
        total_weight = sum(inst.weight * inst.health_score for inst in instances)
        if total_weight == 0:
            return instances[0]
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for inst in instances:
            cumulative += inst.weight * inst.health_score
            if r <= cumulative:
                return inst
        
        return instances[-1]
    
    def update_health(
        self,
        agent_name: str,
        instance_id: str,
        health_score: float,
        response_time_ms: float,
    ) -> None:
        """Update instance health metrics."""
        instances = self._agents.get(agent_name, [])
        for inst in instances:
            if inst.instance_id == instance_id:
                inst.health_score = max(0.0, min(1.0, health_score))
                inst.response_time_ms = response_time_ms
                break
    
    def get_stats(self) -> dict:
        """Get load balancer statistics."""
        stats = {}
        
        for agent_name, instances in self._agents.items():
            stats[agent_name] = {
                "total_instances": len(instances),
                "healthy_instances": sum(1 for inst in instances if inst.health_score > 0.5),
                "total_active_tasks": sum(inst.active_tasks for inst in instances),
                "total_tasks": sum(inst.total_tasks for inst in instances),
                "instances": [
                    {
                        "id": inst.instance_id,
                        "active_tasks": inst.active_tasks,
                        "total_tasks": inst.total_tasks,
                        "health_score": inst.health_score,
                        "response_time_ms": inst.response_time_ms,
                    }
                    for inst in instances
                ],
            }
        
        return stats
