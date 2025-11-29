from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

AgentKind = Literal["sovereign", "specialist"]


@dataclass
class AgentConfig:
    name: str
    role: str
    kind: AgentKind
    description: str
    write_access: bool
    domains: List[str] = field(default_factory=list)


@dataclass
class BrainMetadata:
    name: str
    owner: str
    description: str


@dataclass
class BrainConfig:
    metadata: BrainMetadata
    agents: Dict[str, AgentConfig]
    mcp: Dict[str, Any]
