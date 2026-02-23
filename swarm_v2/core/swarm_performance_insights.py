"""
Swarm V2 Performance Insights Engine
Phase 5: Pulse (Data Analyst)

Generates weekly "Swarm Intelligence Reports" summarizing:
- Global memory growth
- Task success rates
- Resource utilization efficiency
- Agent performance metrics
- Skill acquisition trends

Features:
- Automated weekly report generation
- Trend analysis and forecasting
- Performance scoring and benchmarks
- Exportable reports (JSON, Markdown)
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmPerformanceInsights")


class ReportPeriod(Enum):
    """Report time periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MetricType(Enum):
    """Types of metrics tracked."""
    MEMORY_GROWTH = "memory_growth"
    TASK_SUCCESS = "task_success"
    RESOURCE_UTIL = "resource_utilization"
    AGENT_PERFORMANCE = "agent_performance"
    SKILL_ACQUISITION = "skill_acquisition"
    GPU_EFFICIENCY = "gpu_efficiency"
    MESH_HEALTH = "mesh_health"


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }


@dataclass
class PerformanceMetric:
    """Aggregated performance metric."""
    metric_type: MetricType
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # "improving", "declining", "stable"
    data_points: List[MetricPoint] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "metric_type": self.metric_type.value,
            "current_value": round(self.current_value, 2),
            "previous_value": round(self.previous_value, 2),
            "change_percent": round(self.change_percent, 2),
            "trend": self.trend,
            "data_points": [p.to_dict() for p in self.data_points[-10:]]
        }


@dataclass
class SwarmIntelligenceReport:
    """Complete swarm intelligence report."""
    report_id: str
    period: ReportPeriod
    generated_at: datetime
    start_date: datetime
    end_date: datetime
    
    # Core metrics
    metrics: Dict[str, PerformanceMetric] = field(default_factory=dict)
    
    # Summary scores
    overall_health_score: float = 0.0
    efficiency_score: float = 0.0
    growth_score: float = 0.0
    
    # Insights
    top_performers: List[Dict] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Raw data references
    total_tasks_processed: int = 0
    total_errors: int = 0
    uptime_hours: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "period": self.period.value,
            "generated_at": self.generated_at.isoformat(),
            "date_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat()
            },
            "scores": {
                "overall_health": round(self.overall_health_score, 2),
                "efficiency": round(self.efficiency_score, 2),
                "growth": round(self.growth_score, 2)
            },
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "summary": {
                "total_tasks_processed": self.total_tasks_processed,
                "total_errors": self.total_errors,
                "uptime_hours": round(self.uptime_hours, 2),
                "success_rate": round((self.total_tasks_processed - self.total_errors) / max(1, self.total_tasks_processed) * 100, 2)
            },
            "top_performers": self.top_performers,
            "improvement_areas": self.improvement_areas,
            "recommendations": self.recommendations
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Swarm Intelligence Report",
            f"",
            f"**Report ID:** {self.report_id}",
            f"**Period:** {self.period.value.capitalize()} ({self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')})",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 📊 Overall Scores",
            f"",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| Overall Health | {self.overall_health_score:.1f}/100 |",
            f"| Efficiency | {self.efficiency_score:.1f}/100 |",
            f"| Growth | {self.growth_score:.1f}/100 |",
            f"",
            f"## 📈 Key Metrics",
            f""
        ]
        
        for name, metric in self.metrics.items():
            emoji = "📈" if metric.trend == "improving" else "📉" if metric.trend == "declining" else "➡️"
            lines.append(f"### {emoji} {name.replace('_', ' ').title()}")
            lines.append(f"")
            lines.append(f"- **Current:** {metric.current_value:.2f}")
            lines.append(f"- **Previous:** {metric.previous_value:.2f}")
            lines.append(f"- **Change:** {metric.change_percent:+.1f}%")
            lines.append(f"- **Trend:** {metric.trend}")
            lines.append(f"")
        
        if self.top_performers:
            lines.append(f"## 🏆 Top Performers")
            lines.append(f"")
            for performer in self.top_performers:
                lines.append(f"- **{performer.get('name', 'Unknown')}**: {performer.get('score', 0):.1f} score")
            lines.append(f"")
        
        if self.improvement_areas:
            lines.append(f"## ⚠️ Areas for Improvement")
            lines.append(f"")
            for area in self.improvement_areas:
                lines.append(f"- {area}")
            lines.append(f"")
        
        if self.recommendations:
            lines.append(f"## 💡 Recommendations")
            lines.append(f"")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append(f"")
        
        lines.append(f"## 📋 Summary")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Tasks | {self.total_tasks_processed} |")
        lines.append(f"| Errors | {self.total_errors} |")
        lines.append(f"| Success Rate | {(self.total_tasks_processed - self.total_errors) / max(1, self.total_tasks_processed) * 100:.1f}% |")
        lines.append(f"| Uptime | {self.uptime_hours:.1f} hours |")
        
        return "\n".join(lines)


class SwarmPerformanceInsights:
    """
    Swarm Performance Insights Engine
    
    Collects metrics, generates reports, and provides recommendations
    for swarm optimization.
    """
    
    def __init__(
        self,
        reports_dir: str = "swarm_v2_reports",
        metrics_history_size: int = 1000
    ):
        self.reports_dir = reports_dir
        self.metrics_history_size = metrics_history_size
        
        # Metric history
        self.metric_history: Dict[str, deque] = {}
        
        # Report storage
        self.reports: List[SwarmIntelligenceReport] = []
        
        # Current session stats
        self._session_start = datetime.now()
        self._session_tasks = 0
        self._session_errors = 0
        
        # Running flag
        self._running = False
        
        # Create reports directory
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize metric history
        for metric_type in MetricType:
            self.metric_history[metric_type.value] = deque(maxlen=metrics_history_size)
        
        # Load existing reports
        self._load_reports()
    
    def _load_reports(self):
        """Load existing reports from disk."""
        report_index = os.path.join(self.reports_dir, "report_index.json")
        if os.path.exists(report_index):
            try:
                with open(report_index, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Just load the index, not full reports
                logger.info(f"Loaded report index with {len(data.get('reports', []))} entries")
            except Exception as e:
                logger.warning(f"Could not load report index: {e}")
    
    def _save_report(self, report: SwarmIntelligenceReport):
        """Save report to disk."""
        # Save full report as JSON
        report_file = os.path.join(self.reports_dir, f"{report.report_id}.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        
        # Save as markdown
        md_file = os.path.join(self.reports_dir, f"{report.report_id}.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        
        # Update index
        index_file = os.path.join(self.reports_dir, "report_index.json")
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except:
            index_data = {"reports": []}
        
        index_data["reports"].append({
            "report_id": report.report_id,
            "period": report.period.value,
            "generated_at": report.generated_at.isoformat(),
            "health_score": report.overall_health_score
        })
        
        # Keep only last 52 reports (1 year of weekly)
        index_data["reports"] = index_data["reports"][-52:]
        
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Saved report: {report.report_id}")
    
    def record_metric(self, metric_type: MetricType, value: float, metadata: Dict = None):
        """Record a metric data point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            metadata=metadata or {}
        )
        self.metric_history[metric_type.value].append(point)
    
    def record_task(self, success: bool = True):
        """Record a task execution."""
        self._session_tasks += 1
        if not success:
            self._session_errors += 1
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics from all swarm components."""
        metrics = {}
        
        # Global Memory metrics
        try:
            from swarm_v2.core.global_memory import get_global_memory
            memory = get_global_memory()
            stats = memory.get_stats()
            metrics["memory_total_entries"] = stats.get("total_entries", 0)
            metrics["memory_sync_count"] = stats.get("sync_count", 0)
            self.record_metric(MetricType.MEMORY_GROWTH, metrics["memory_total_entries"])
        except Exception as e:
            logger.warning(f"Could not collect memory metrics: {e}")
            metrics["memory_total_entries"] = 0
        
        # Task Arbiter metrics
        try:
            from swarm_v2.core.task_arbiter import get_task_arbiter
            arbiter = get_task_arbiter()
            status = arbiter.get_system_status()
            metrics["cpu_usage"] = status.get("cpu", {}).get("usage_percent", 0)
            metrics["memory_usage"] = status.get("memory", {}).get("percent_used", 0)
            metrics["queued_tasks"] = status.get("tasks", {}).get("queued", 0)
            self.record_metric(MetricType.RESOURCE_UTIL, metrics["cpu_usage"])
        except Exception as e:
            logger.warning(f"Could not collect arbiter metrics: {e}")
            metrics["cpu_usage"] = 0
        
        # Mesh health
        try:
            from swarm_v2.core.agent_mesh import get_agent_mesh
            mesh = get_agent_mesh()
            mesh_stats = mesh.get_stats()
            metrics["mesh_nodes"] = mesh_stats.get("node_count", 0)
            metrics["mesh_messages"] = mesh_stats.get("message_count", 0)
            self.record_metric(MetricType.MESH_HEALTH, metrics["mesh_nodes"])
        except Exception as e:
            logger.warning(f"Could not collect mesh metrics: {e}")
            metrics["mesh_nodes"] = 0
        
        # Learning Engine metrics
        try:
            from swarm_v2.skills.learning_engine import get_learning_engine
            engine = get_learning_engine()
            learn_stats = engine.get_stats()
            metrics["learned_skills"] = learn_stats.get("skills_count", 0)
            self.record_metric(MetricType.SKILL_ACQUISITION, metrics["learned_skills"])
        except Exception as e:
            logger.warning(f"Could not collect learning metrics: {e}")
            metrics["learned_skills"] = 0
        
        # Synthesizer metrics
        try:
            from swarm_v2.mcp.synthesizer import get_synthesizer
            synthesizer = get_synthesizer()
            synth_stats = synthesizer.get_stats()
            metrics["synthesized_tools"] = synth_stats.get("tools_count", 0)
        except Exception as e:
            logger.warning(f"Could not collect synthesizer metrics: {e}")
            metrics["synthesized_tools"] = 0
        
        # Self-healing metrics
        try:
            from swarm_v2.core.self_healing_infra import get_self_healing_infra
            infra = get_self_healing_infra()
            infra_status = infra.get_status()
            metrics["infra_restarts"] = infra_status.get("total_restarts", 0)
        except Exception as e:
            logger.warning(f"Could not collect infra metrics: {e}")
            metrics["infra_restarts"] = 0
        
        # Security metrics
        try:
            from swarm_v2.core.neural_wall import get_neural_wall
            wall = get_neural_wall()
            wall_stats = wall.get_stats()
            metrics["threats_blocked"] = wall_stats.get("total_detections", 0)
        except Exception as e:
            logger.warning(f"Could not collect security metrics: {e}")
            metrics["threats_blocked"] = 0
        
        # Calculate task success rate
        if self._session_tasks > 0:
            success_rate = (self._session_tasks - self._session_errors) / self._session_tasks * 100
            self.record_metric(MetricType.TASK_SUCCESS, success_rate)
            metrics["task_success_rate"] = success_rate
        
        return metrics
    
    def _calculate_trend(self, current: float, previous: float) -> str:
        """Determine trend direction."""
        if previous == 0:
            return "stable"
        change = (current - previous) / previous * 100
        if change > 5:
            return "improving"
        elif change < -5:
            return "declining"
        return "stable"
    
    def _get_previous_metric_value(self, metric_type: MetricType) -> float:
        """Get the previous metric value from history."""
        history = self.metric_history.get(metric_type.value, [])
        if len(history) >= 2:
            return history[-2].value
        elif len(history) == 1:
            return history[0].value
        return 0.0
    
    async def generate_report(self, period: ReportPeriod = ReportPeriod.WEEKLY) -> SwarmIntelligenceReport:
        """Generate a comprehensive swarm intelligence report."""
        
        # Determine date range
        end_date = datetime.now()
        if period == ReportPeriod.DAILY:
            start_date = end_date - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            start_date = end_date - timedelta(weeks=1)
        else:  # MONTHLY
            start_date = end_date - timedelta(days=30)
        
        # Collect current metrics
        current_metrics = await self.collect_metrics()
        
        # Create report
        report = SwarmIntelligenceReport(
            report_id=f"report_{period.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            period=period,
            generated_at=datetime.now(),
            start_date=start_date,
            end_date=end_date,
            total_tasks_processed=self._session_tasks,
            total_errors=self._session_errors,
            uptime_hours=(datetime.now() - self._session_start).total_seconds() / 3600
        )
        
        # Build performance metrics
        metric_mappings = [
            ("memory_growth", MetricType.MEMORY_GROWTH, current_metrics.get("memory_total_entries", 0)),
            ("task_success_rate", MetricType.TASK_SUCCESS, current_metrics.get("task_success_rate", 100)),
            ("resource_utilization", MetricType.RESOURCE_UTIL, current_metrics.get("cpu_usage", 0)),
            ("skill_acquisition", MetricType.SKILL_ACQUISITION, current_metrics.get("learned_skills", 0)),
            ("mesh_health", MetricType.MESH_HEALTH, current_metrics.get("mesh_nodes", 0)),
        ]
        
        for name, metric_type, current_value in metric_mappings:
            previous_value = self._get_previous_metric_value(metric_type)
            change = ((current_value - previous_value) / max(1, previous_value)) * 100 if previous_value > 0 else 0
            
            history = list(self.metric_history.get(metric_type.value, []))
            
            report.metrics[name] = PerformanceMetric(
                metric_type=metric_type,
                current_value=current_value,
                previous_value=previous_value,
                change_percent=change,
                trend=self._calculate_trend(current_value, previous_value),
                data_points=history
            )
        
        # Calculate overall scores
        task_success = current_metrics.get("task_success_rate", 100)
        cpu_efficiency = 100 - min(100, current_metrics.get("cpu_usage", 0))
        memory_growth = min(100, current_metrics.get("memory_total_entries", 0) / 10)
        
        report.overall_health_score = (task_success + cpu_efficiency + memory_growth) / 3
        report.efficiency_score = cpu_efficiency
        report.growth_score = memory_growth
        
        # Identify top performers
        try:
            from swarm_v2.core.agent_mesh import get_agent_mesh
            mesh = get_agent_mesh()
            topology = mesh.get_topology()
            for node in topology.get("nodes", [])[:3]:
                report.top_performers.append({
                    "name": node.get("name", "Unknown"),
                    "role": node.get("role", ""),
                    "score": node.get("message_count", 0)
                })
        except:
            pass
        
        # Generate improvement areas
        if task_success < 90:
            report.improvement_areas.append("Task success rate below 90% - investigate error patterns")
        if cpu_efficiency < 50:
            report.improvement_areas.append("High CPU utilization - consider load balancing")
        if memory_growth < 10:
            report.improvement_areas.append("Low memory growth - increase knowledge acquisition")
        
        # Generate recommendations
        if report.overall_health_score > 80:
            report.recommendations.append("Swarm is performing well - maintain current configuration")
        else:
            report.recommendations.append("Review agent task distribution for optimization")
        
        if current_metrics.get("learned_skills", 0) < 5:
            report.recommendations.append("Increase skill acquisition through documentation ingestion")
        
        if current_metrics.get("threats_blocked", 0) > 0:
            report.recommendations.append(f"Review {current_metrics['threats_blocked']} blocked threats for patterns")
        
        # Save report
        self._save_report(report)
        self.reports.append(report)
        
        return report
    
    async def monitor_loop(self, interval_hours: int = 168):  # Default: weekly
        """Background loop for periodic report generation."""
        self._running = True
        logger.info(f"Performance Insights monitor started (interval: {interval_hours}h)")
        
        while self._running:
            try:
                # Generate weekly report
                report = await self.generate_report(ReportPeriod.WEEKLY)
                logger.info(f"Generated report: {report.report_id} (health: {report.overall_health_score:.1f})")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Report generation error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        logger.info("Performance Insights monitor stopped")
    
    def get_status(self) -> Dict:
        """Get current status."""
        return {
            "running": self._running,
            "session_start": self._session_start.isoformat(),
            "session_tasks": self._session_tasks,
            "session_errors": self._session_errors,
            "reports_generated": len(self.reports),
            "metrics_tracked": {
                metric: len(history) 
                for metric, history in self.metric_history.items()
            }
        }
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict]:
        """Get recent reports."""
        return [r.to_dict() for r in self.reports[-limit:]]
    
    def get_metric_history(self, metric_type: MetricType, limit: int = 100) -> List[Dict]:
        """Get history for a specific metric."""
        history = list(self.metric_history.get(metric_type.value, []))[-limit:]
        return [p.to_dict() for p in history]


# Singleton
_insights: Optional[SwarmPerformanceInsights] = None

def get_performance_insights() -> SwarmPerformanceInsights:
    """Get or create the performance insights singleton."""
    global _insights
    if _insights is None:
        _insights = SwarmPerformanceInsights()
    return _insights

async def start_performance_monitoring(interval_hours: int = 168):
    """Start the performance monitoring loop."""
    insights = get_performance_insights()
    await insights.monitor_loop(interval_hours)


if __name__ == "__main__":
    # Demo
    async def demo():
        insights = SwarmPerformanceInsights()
        
        # Record some sample metrics
        insights.record_task(success=True)
        insights.record_task(success=True)
        insights.record_task(success=False)
        insights.record_metric(MetricType.MEMORY_GROWTH, 42.5)
        insights.record_metric(MetricType.RESOURCE_UTIL, 35.2)
        
        # Generate report
        report = await insights.generate_report(ReportPeriod.WEEKLY)
        
        print(f"Report: {report.report_id}")
        print(f"Health Score: {report.overall_health_score:.1f}")
        print(f"Tasks: {report.total_tasks_processed}")
        print("\nMarkdown Report:")
        print(report.to_markdown()[:500])
    
    asyncio.run(demo())