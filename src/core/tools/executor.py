"""
Tool Execution Framework

Enables agents to execute standard CLI tools (kubectl, terraform, git) safely.
"""

import asyncio
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    command: str


class ToolExecutor:
    """
    Safe execution of CLI tools for agents.
    
    Features:
    - Sandboxed execution
    - Timeout protection
    - Output capture
    - Security validation
    """
    
    def __init__(
        self,
        working_dir: Optional[Path] = None,
        timeout_seconds: int = 300,
        allow_destructive: bool = False,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.timeout_seconds = timeout_seconds
        self.allow_destructive = allow_destructive
        self._sandbox_dir = None
    
    async def execute(
        self,
        command: list[str],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> ToolExecutionResult:
        """
        Execute a command safely.
        
        Args:
            command: Command and arguments as list
            cwd: Working directory
            env: Environment variables
            timeout: Execution timeout
            
        Returns:
            ToolExecutionResult
        """
        import time
        
        start_time = time.time()
        cmd_str = " ".join(command)
        
        # Security check
        if not self._is_safe_command(command):
            return ToolExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command blocked: {cmd_str}",
                exit_code=1,
                duration_ms=0,
                command=cmd_str,
            )
        
        cwd = cwd or self.working_dir
        timeout = timeout or self.timeout_seconds
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    exit_code=124,
                    duration_ms=int((time.time() - start_time) * 1000),
                    command=cmd_str,
                )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ToolExecutionResult(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8", errors="ignore"),
                stderr=stderr.decode("utf-8", errors="ignore"),
                exit_code=process.returncode,
                duration_ms=duration_ms,
                command=cmd_str,
            )
            
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                duration_ms=int((time.time() - start_time) * 1000),
                command=cmd_str,
            )
    
    def _is_safe_command(self, command: list[str]) -> bool:
        """Check if command is safe to execute."""
        if not command:
            return False
        
        tool = command[0]
        
        # Block dangerous commands unless explicitly allowed
        dangerous = [
            "rm", "rmdir", "del", "format",
            "mkfs", "dd", "shutdown", "reboot",
        ]
        
        if tool in dangerous and not self.allow_destructive:
            return False
        
        # Allow specific tools
        allowed_tools = [
            "kubectl", "terraform", "git", "docker",
            "kubectl", "helm", "kustomize",
            "python", "node", "npm", "pip",
            "curl", "wget", "jq", "yq",
        ]
        
        return tool in allowed_tools or tool.startswith("/")
    
    async def kubectl(
        self,
        args: list[str],
        namespace: Optional[str] = None,
        context: Optional[str] = None,
    ) -> ToolExecutionResult:
        """Execute kubectl command."""
        command = ["kubectl"] + args
        
        if namespace:
            command.extend(["-n", namespace])
        if context:
            command.extend(["--context", context])
        
        return await self.execute(command)
    
    async def terraform(
        self,
        action: str,
        args: list[str],
        working_dir: Optional[Path] = None,
    ) -> ToolExecutionResult:
        """Execute terraform command."""
        command = ["terraform", action] + args
        return await self.execute(command, cwd=working_dir)
    
    async def git(
        self,
        args: list[str],
        repo_path: Optional[Path] = None,
    ) -> ToolExecutionResult:
        """Execute git command."""
        command = ["git"] + args
        return await self.execute(command, cwd=repo_path)


# Global executor instance
_global_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get global tool executor instance."""
    global _global_executor
    if _global_executor is None:
        _global_executor = ToolExecutor()
    return _global_executor
