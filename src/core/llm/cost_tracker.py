"""
LLM Cost Tracking

Tracks and budgets LLM API costs across providers.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# Cost per 1M tokens (approximate, as of 2024)
COST_PER_MILLION_TOKENS = {
    "openai": {
        "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus": {"input": 15.0, "output": 75.0},
    },
    "gemini": {
        "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    },
}


@dataclass
class CostEntry:
    """A single cost entry."""
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class Budget:
    """Budget configuration."""
    total_budget_usd: float
    daily_budget_usd: Optional[float] = None
    monthly_budget_usd: Optional[float] = None
    per_user_budget_usd: Optional[float] = None
    alert_threshold: float = 0.8  # Alert at 80% of budget
    reset_period: str = "monthly"  # daily, weekly, monthly


class CostTracker:
    """
    Tracks LLM API costs and enforces budgets.
    
    Features:
    - Per-provider cost tracking
    - Budget enforcement
    - Cost alerts
    - Usage analytics
    """
    
    def __init__(self, budget: Optional[Budget] = None):
        self.budget = budget
        self._entries: list[CostEntry] = []
        self._daily_costs: dict[str, float] = {}  # date -> cost
        self._monthly_costs: dict[str, float] = {}  # YYYY-MM -> cost
        self._user_costs: dict[str, float] = {}  # user_id -> cost
        self._alerts_sent: set[str] = set()
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculate cost for a request.
        
        Args:
            provider: LLM provider
            model: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            
        Returns:
            Cost in USD
        """
        costs = COST_PER_MILLION_TOKENS.get(provider, {}).get(model)
        if not costs:
            # Default fallback
            logger.warning(f"Unknown cost for {provider}/{model}, using default")
            costs = {"input": 1.0, "output": 2.0}
        
        input_cost = (prompt_tokens / 1_000_000) * costs["input"]
        output_cost = (completion_tokens / 1_000_000) * costs["output"]
        
        return input_cost + output_cost
    
    def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> CostEntry:
        """
        Record LLM usage and calculate cost.
        
        Returns:
            CostEntry with calculated cost
        """
        cost = self.calculate_cost(provider, model, prompt_tokens, completion_tokens)
        
        entry = CostEntry(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            user_id=user_id,
            project_id=project_id,
        )
        
        self._entries.append(entry)
        
        # Update aggregated costs
        date_key = entry.timestamp.date().isoformat()
        month_key = entry.timestamp.strftime("%Y-%m")
        
        self._daily_costs[date_key] = self._daily_costs.get(date_key, 0) + cost
        self._monthly_costs[month_key] = self._monthly_costs.get(month_key, 0) + cost
        
        if user_id:
            self._user_costs[user_id] = self._user_costs.get(user_id, 0) + cost
        
        # Check budget
        if self.budget:
            self._check_budget(entry)
        
        logger.debug(
            f"Recorded cost: ${cost:.4f} for {provider}/{model} "
            f"({prompt_tokens + completion_tokens} tokens)"
        )
        
        return entry
    
    def _check_budget(self, entry: CostEntry) -> None:
        """Check if budget limits are exceeded."""
        if not self.budget:
            return
        
        total_cost = self.get_total_cost()
        
        # Check total budget
        if total_cost >= self.budget.total_budget_usd:
            self._send_alert("total_budget_exceeded", total_cost)
            return
        
        # Check daily budget
        if self.budget.daily_budget_usd:
            today = datetime.utcnow().date().isoformat()
            daily_cost = self._daily_costs.get(today, 0)
            if daily_cost >= self.budget.daily_budget_usd:
                self._send_alert("daily_budget_exceeded", daily_cost)
        
        # Check monthly budget
        if self.budget.monthly_budget_usd:
            month = datetime.utcnow().strftime("%Y-%m")
            monthly_cost = self._monthly_costs.get(month, 0)
            if monthly_cost >= self.budget.monthly_budget_usd:
                self._send_alert("monthly_budget_exceeded", monthly_cost)
        
        # Check per-user budget
        if self.budget.per_user_budget_usd and entry.user_id:
            user_cost = self._user_costs.get(entry.user_id, 0)
            if user_cost >= self.budget.per_user_budget_usd:
                self._send_alert(f"user_budget_exceeded:{entry.user_id}", user_cost)
        
        # Check alert threshold
        threshold = self.budget.total_budget_usd * self.budget.alert_threshold
        if total_cost >= threshold and "threshold_alert" not in self._alerts_sent:
            self._send_alert("budget_threshold", total_cost)
            self._alerts_sent.add("threshold_alert")
    
    def _send_alert(self, alert_type: str, cost: float) -> None:
        """Send budget alert."""
        if alert_type in self._alerts_sent:
            return
        
        logger.warning(
            f"Budget alert: {alert_type} - Cost: ${cost:.2f}, "
            f"Budget: ${self.budget.total_budget_usd:.2f}"
        )
        
        # In production, would send to alerting system
        self._alerts_sent.add(alert_type)
    
    def get_total_cost(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Get total cost for a time period."""
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        return sum(e.cost_usd for e in entries)
    
    def get_cost_by_provider(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, float]:
        """Get cost breakdown by provider."""
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        costs = {}
        for entry in entries:
            costs[entry.provider] = costs.get(entry.provider, 0) + entry.cost_usd
        
        return costs
    
    def get_cost_by_model(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, float]:
        """Get cost breakdown by model."""
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        costs = {}
        for entry in entries:
            key = f"{entry.provider}/{entry.model}"
            costs[key] = costs.get(key, 0) + entry.cost_usd
        
        return costs
    
    def get_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get comprehensive usage statistics."""
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        total_tokens = sum(e.prompt_tokens + e.completion_tokens for e in entries)
        total_cost = sum(e.cost_usd for e in entries)
        
        return {
            "total_requests": len(entries),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "average_cost_per_request": total_cost / max(len(entries), 1),
            "cost_by_provider": self.get_cost_by_provider(start_date, end_date),
            "cost_by_model": self.get_cost_by_model(start_date, end_date),
            "daily_costs": dict(self._daily_costs),
            "monthly_costs": dict(self._monthly_costs),
        }
