"""
Workflow Scheduler

Handles scheduled workflow execution with cron-like syntax.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional
from croniter import croniter

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    """
    Schedules workflows for execution based on cron expressions.
    
    Features:
    - Cron-based scheduling
    - One-time scheduled execution
    - Recurring workflows
    - Timezone support
    """
    
    def __init__(self, workflow_engine):
        self.workflow_engine = workflow_engine
        self._schedules: dict[str, dict] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def schedule(
        self,
        workflow_id: str,
        cron_expression: str,
        context: Optional[dict] = None,
        enabled: bool = True,
    ) -> str:
        """
        Schedule a workflow to run on a cron schedule.
        
        Args:
            workflow_id: Workflow to schedule
            cron_expression: Cron expression (e.g., "0 2 * * *" for daily at 2 AM)
            context: Optional context to pass to workflow
            enabled: Whether schedule is active
            
        Returns:
            Schedule ID
        """
        schedule_id = f"{workflow_id}_{cron_expression}"
        
        # Validate cron expression
        try:
            croniter(cron_expression, datetime.now())
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        self._schedules[schedule_id] = {
            "workflow_id": workflow_id,
            "cron": cron_expression,
            "context": context or {},
            "enabled": enabled,
            "next_run": self._calculate_next_run(cron_expression),
            "last_run": None,
            "run_count": 0,
        }
        
        logger.info(f"Scheduled workflow {workflow_id} with cron {cron_expression}")
        return schedule_id
    
    def schedule_once(
        self,
        workflow_id: str,
        run_at: datetime,
        context: Optional[dict] = None,
    ) -> str:
        """Schedule a workflow to run once at a specific time."""
        schedule_id = f"{workflow_id}_once_{run_at.timestamp()}"
        
        self._schedules[schedule_id] = {
            "workflow_id": workflow_id,
            "cron": None,
            "run_at": run_at,
            "context": context or {},
            "enabled": True,
            "one_time": True,
            "run_count": 0,
        }
        
        logger.info(f"Scheduled one-time workflow {workflow_id} for {run_at}")
        return schedule_id
    
    def unschedule(self, schedule_id: str) -> bool:
        """Remove a schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            logger.info(f"Unscheduled {schedule_id}")
            return True
        return False
    
    def enable(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id]["enabled"] = True
            return True
        return False
    
    def disable(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id]["enabled"] = False
            return True
        return False
    
    def list_schedules(self) -> list[dict]:
        """List all schedules."""
        return [
            {
                "id": sid,
                "workflow_id": s["workflow_id"],
                "cron": s.get("cron"),
                "enabled": s["enabled"],
                "next_run": s.get("next_run"),
                "last_run": s.get("last_run"),
                "run_count": s.get("run_count", 0),
            }
            for sid, s in self._schedules.items()
        ]
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Workflow scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Workflow scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                now = datetime.utcnow()
                ready = []
                
                # Check all schedules
                for schedule_id, schedule in self._schedules.items():
                    if not schedule.get("enabled", True):
                        continue
                    
                    # Check one-time schedules
                    if schedule.get("one_time"):
                        run_at = schedule.get("run_at")
                        if run_at and now >= run_at:
                            ready.append(schedule_id)
                    
                    # Check cron schedules
                    elif schedule.get("cron"):
                        next_run = schedule.get("next_run")
                        if next_run and now >= next_run:
                            ready.append(schedule_id)
                
                # Execute ready workflows
                for schedule_id in ready:
                    await self._execute_scheduled(schedule_id)
                
                # Sleep for a short interval
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_scheduled(self, schedule_id: str) -> None:
        """Execute a scheduled workflow."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return
        
        workflow_id = schedule["workflow_id"]
        context = schedule.get("context", {})
        
        try:
            logger.info(f"Executing scheduled workflow {workflow_id}")
            
            # Execute workflow
            result = await self.workflow_engine.run(workflow_id, context)
            
            # Update schedule
            schedule["last_run"] = datetime.utcnow().isoformat()
            schedule["run_count"] = schedule.get("run_count", 0) + 1
            
            # Remove one-time schedules
            if schedule.get("one_time"):
                del self._schedules[schedule_id]
            else:
                # Calculate next run for cron schedules
                schedule["next_run"] = self._calculate_next_run(schedule["cron"])
            
            logger.info(f"Scheduled workflow {workflow_id} completed: {result.status.value}")
            
        except Exception as e:
            logger.error(f"Failed to execute scheduled workflow {workflow_id}: {e}")
            schedule["last_run"] = datetime.utcnow().isoformat()
            schedule["error"] = str(e)
    
    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression."""
        cron = croniter(cron_expression, datetime.utcnow())
        return cron.get_next(datetime)
