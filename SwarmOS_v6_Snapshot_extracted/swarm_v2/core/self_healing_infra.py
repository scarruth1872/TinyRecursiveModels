"""
Swarm V2 Self-Healing Infrastructure
Phase 5: Flow (DevOps Engineer)

Automatically monitors and restarts the Swarm OS API and Dashboard
if connectivity heartbeats fail for more than 60 seconds.

This provides infrastructure-level self-healing independent of agent-level recovery.
"""

import asyncio
import subprocess
import time
import logging
import os
import signal
import psutil
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNRESPONSIVE = "unresponsive"
    RESTARTING = "restarting"
    STOPPED = "stopped"


@dataclass
class ServiceConfig:
    """Configuration for a monitored service."""
    name: str
    health_endpoint: str
    restart_command: List[str]
    port: int
    heartbeat_timeout: int = 60  # Seconds before restart
    restart_cooldown: int = 30   # Seconds between restart attempts
    max_restart_attempts: int = 3


@dataclass
class ServiceHealth:
    """Health status of a monitored service."""
    service_name: str
    status: ServiceStatus
    last_heartbeat: float
    last_response_time: float
    consecutive_failures: int
    restart_count: int
    last_restart: Optional[float] = None
    error_message: str = ""
    pid: Optional[int] = None


class SelfHealingInfra:
    """
    Infrastructure-level self-healing system.
    
    Monitors API and Dashboard services, automatically restarting them
    if heartbeat checks fail for more than the configured timeout.
    """
    
    def __init__(self, check_interval: int = 10):
        self.check_interval = check_interval
        self.running = False
        self.services: Dict[str, ServiceConfig] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self.restart_history: List[Dict[str, Any]] = []
        
        # Configure logging
        self.logger = logging.getLogger("SelfHealingInfra")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] [SelfHealing] %(message)s"
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Default services to monitor
        self._register_default_services()
    
    def _register_default_services(self):
        """Register the default Swarm OS services."""
        # Swarm API
        self.register_service(ServiceConfig(
            name="swarm_api",
            health_endpoint="http://localhost:8001/health",
            restart_command=["python", "-m", "uvicorn", "swarm_v2.app_v2:app", "--host", "0.0.0.0", "--port", "8001"],
            port=8001,
            heartbeat_timeout=60,
            restart_cooldown=30,
            max_restart_attempts=3
        ))
        
        # Dashboard (Vite dev server)
        self.register_service(ServiceConfig(
            name="swarm_dashboard",
            health_endpoint="http://localhost:5173/",
            restart_command=["npm", "run", "dev"],
            port=5173,
            heartbeat_timeout=60,
            restart_cooldown=30,
            max_restart_attempts=3,
        ))
        
        # Dashboard v2 (if running)
        self.register_service(ServiceConfig(
            name="swarm_dashboard_v2",
            health_endpoint="http://localhost:5174/",
            restart_command=["npm", "run", "dev", "--", "--port", "5174"],
            port=5174,
            heartbeat_timeout=60,
            restart_cooldown=30,
            max_restart_attempts=3,
        ))
    
    def register_service(self, config: ServiceConfig):
        """Register a service to monitor."""
        self.services[config.name] = config
        self.health_status[config.name] = ServiceHealth(
            service_name=config.name,
            status=ServiceStatus.STOPPED,
            last_heartbeat=0,
            last_response_time=0,
            consecutive_failures=0,
            restart_count=0
        )
        self.logger.info(f"Registered service: {config.name} on port {config.port}")
    
    async def start(self):
        """Start the self-healing monitoring loop."""
        self.running = True
        self.logger.info("Self-Healing Infrastructure started. Monitoring services...")
        
        while self.running:
            try:
                for service_name, config in self.services.items():
                    await self._check_service_health(service_name, config)
                
                # Log summary
                self._log_health_summary()
                
            except Exception as e:
                self.logger.error(f"Error in self-healing loop: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        self.logger.info("Self-Healing Infrastructure stopped.")
    
    async def _check_service_health(self, service_name: str, config: ServiceConfig):
        """Check health of a single service."""
        health = self.health_status[service_name]
        current_time = time.time()
        
        # Check if service is responding
        is_responsive, response_time = await self._ping_service(config.health_endpoint)
        
        if is_responsive:
            health.status = ServiceStatus.HEALTHY
            health.last_heartbeat = current_time
            health.last_response_time = response_time
            health.consecutive_failures = 0
            health.error_message = ""
            
            # Try to get PID
            health.pid = self._find_process_on_port(config.port)
        else:
            health.consecutive_failures += 1
            health.error_message = f"Health check failed ({health.consecutive_failures} consecutive)"
            
            # Calculate time since last successful heartbeat
            time_since_heartbeat = current_time - health.last_heartbeat if health.last_heartbeat > 0 else float('inf')
            
            # Check if we need to restart
            if time_since_heartbeat > config.heartbeat_timeout:
                self.logger.warning(
                    f"[{service_name}] Unresponsive for {int(time_since_heartbeat)}s "
                    f"(timeout: {config.heartbeat_timeout}s). Initiating restart..."
                )
                await self._restart_service(service_name, config, health)
            else:
                health.status = ServiceStatus.DEGRADED
                self.logger.warning(
                    f"[{service_name}] Degraded - {int(time_since_heartbeat)}s since last heartbeat"
                )
    
    async def _ping_service(self, endpoint: str, timeout: float = 5.0) -> tuple[bool, float]:
        """Ping a service health endpoint."""
        start_time = time.time()
        try:
            # Use urllib for synchronous request, wrapped in async
            loop = asyncio.get_event_loop()
            
            def _sync_ping():
                try:
                    req = urllib.request.Request(endpoint)
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        return response.status == 200
                except Exception:
                    return False
            
            result = await loop.run_in_executor(None, _sync_ping)
            response_time = time.time() - start_time
            return result, response_time
        except Exception as e:
            return False, 0.0
    
    def _find_process_on_port(self, port: int) -> Optional[int]:
        """Find the PID of the process listening on a port."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return conn.pid
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return None
    
    async def _restart_service(self, service_name: str, config: ServiceConfig, health: ServiceHealth):
        """Restart an unresponsive service."""
        current_time = time.time()
        
        # Check cooldown
        if health.last_restart:
            time_since_restart = current_time - health.last_restart
            if time_since_restart < config.restart_cooldown:
                self.logger.info(
                    f"[{service_name}] In cooldown ({int(time_since_restart)}s / {config.restart_cooldown}s)"
                )
                return
        
        # Check max restart attempts
        if health.restart_count >= config.max_restart_attempts:
            self.logger.error(
                f"[{service_name}] Max restart attempts ({config.max_restart_attempts}) reached. "
                f"Manual intervention required."
            )
            health.status = ServiceStatus.STOPPED
            return
        
        health.status = ServiceStatus.RESTARTING
        health.restart_count += 1
        health.last_restart = current_time
        
        self.logger.info(f"[{service_name}] Restarting (attempt {health.restart_count}/{config.max_restart_attempts})...")
        
        # Kill existing process if found
        if health.pid:
            try:
                proc = psutil.Process(health.pid)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()
                self.logger.info(f"[{service_name}] Terminated old process (PID: {health.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.warning(f"[{service_name}] Could not terminate process: {e}")
        
        # Also try to kill by port
        self._kill_process_on_port(config.port)
        
        # Start new process
        try:
            # Determine working directory
            cwd = os.getcwd()
            if "dashboard" in service_name:
                dashboard_path = os.path.join(cwd, "swarm_v2_artifacts", "dashboard-v2")
                if os.path.exists(dashboard_path):
                    cwd = dashboard_path
            
            # Start the service
            process = subprocess.Popen(
                config.restart_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                start_new_session=True  # Detach from parent
            )
            
            health.pid = process.pid
            self.logger.info(f"[{service_name}] Started new process (PID: {process.pid})")
            
            # Record restart in history
            self.restart_history.append({
                "service": service_name,
                "timestamp": datetime.now().isoformat(),
                "attempt": health.restart_count,
                "pid": process.pid,
                "command": " ".join(config.restart_command)
            })
            
            # Wait a moment and verify
            await asyncio.sleep(5)
            is_responsive, _ = await self._ping_service(config.health_endpoint)
            
            if is_responsive:
                health.status = ServiceStatus.HEALTHY
                health.last_heartbeat = time.time()
                health.consecutive_failures = 0
                health.restart_count = 0  # Reset on successful restart
                self.logger.info(f"[{service_name}] Successfully restarted!")
            else:
                health.status = ServiceStatus.UNRESPONSIVE
                self.logger.warning(f"[{service_name}] Restarted but not yet responsive")
                
        except Exception as e:
            self.logger.error(f"[{service_name}] Failed to restart: {e}")
            health.status = ServiceStatus.STOPPED
            health.error_message = str(e)
    
    def _kill_process_on_port(self, port: int):
        """Kill any process listening on the specified port."""
        try:
            pid = self._find_process_on_port(port)
            if pid:
                proc = psutil.Process(pid)
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    proc.kill()
                self.logger.info(f"Killed process on port {port} (PID: {pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def _log_health_summary(self):
        """Log a summary of all service health."""
        summary = []
        for name, health in self.health_status.items():
            status_emoji = {
                ServiceStatus.HEALTHY: "✅",
                ServiceStatus.DEGRADED: "⚠️",
                ServiceStatus.UNRESPONSIVE: "❌",
                ServiceStatus.RESTARTING: "🔄",
                ServiceStatus.STOPPED: "⏹️"
            }.get(health.status, "❓")
            summary.append(f"{name}: {status_emoji} {health.status.value}")
        
        # Only log every 6 checks (60 seconds with 10s interval)
        if not hasattr(self, '_check_count'):
            self._check_count = 0
        self._check_count += 1
        
        if self._check_count % 6 == 0:
            self.logger.info(f"Health Summary: {' | '.join(summary)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of all services."""
        return {
            "running": self.running,
            "services": {
                name: {
                    "status": health.status.value,
                    "last_heartbeat": health.last_heartbeat,
                    "last_response_time_ms": round(health.last_response_time * 1000, 2),
                    "consecutive_failures": health.consecutive_failures,
                    "restart_count": health.restart_count,
                    "pid": health.pid,
                    "error": health.error_message
                }
                for name, health in self.health_status.items()
            },
            "restart_history": self.restart_history[-10:],
            "total_restarts": len(self.restart_history)
        }
    
    def force_restart(self, service_name: str) -> Dict[str, Any]:
        """Force a restart of a specific service."""
        if service_name not in self.services:
            return {"error": f"Service '{service_name}' not found"}
        
        config = self.services[service_name]
        health = self.health_status[service_name]
        
        # Create task for async restart
        asyncio.create_task(self._restart_service(service_name, config, health))
        
        return {
            "status": "initiated",
            "service": service_name,
            "message": f"Restart initiated for {service_name}"
        }
    
    def reset_restart_count(self, service_name: str) -> Dict[str, Any]:
        """Reset the restart counter for a service."""
        if service_name not in self.health_status:
            return {"error": f"Service '{service_name}' not found"}
        
        health = self.health_status[service_name]
        health.restart_count = 0
        return {"status": "reset", "service": service_name}


# Singleton instance
_self_healing_infra: Optional[SelfHealingInfra] = None

def get_self_healing_infra() -> SelfHealingInfra:
    """Get or create the SelfHealingInfra singleton."""
    global _self_healing_infra
    if _self_healing_infra is None:
        _self_healing_infra = SelfHealingInfra()
    return _self_healing_infra

async def start_self_healing():
    """Start the self-healing infrastructure."""
    infra = get_self_healing_infra()
    await infra.start()

async def stop_self_healing():
    """Stop the self-healing infrastructure."""
    infra = get_self_healing_infra()
    await infra.stop()


if __name__ == "__main__":
    # Standalone run for testing
    async def main():
        infra = SelfHealingInfra()
        try:
            await infra.start()
        except KeyboardInterrupt:
            await infra.stop()
    
    asyncio.run(main())