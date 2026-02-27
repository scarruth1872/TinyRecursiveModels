
from swarm_v2.core.base_agent import AgentPersona, BaseAgent
from swarm_v2.skills.file_skill import (
    FileSkill, WebSearchSkill,
    CodeAnalysisSkill, DataSkill, DocSkill
)
from swarm_v2.skills.hardened_shell_skill import HardenedShellSkill as ShellSkill
from swarm_v2.skills.doc_ingestion_skill import DocIngestionSkill
from swarm_v2.skills.mcp_tool_skill import MCPToolSkill
from swarm_v2.skills.embedding_skill import EmbeddingSkill, FastEmbeddingSkill, HighQualityEmbeddingSkill, SpectralEmbeddingSkill
from swarm_v2.skills.trm_skill import TRMSkill
from swarm_v2.skills.relationship_skill import RelationshipReasoningSkill

# Cognitive Stack Configuration (Phase 6)
# Each agent uses Gemma 3 270M (Executive) + Samsung TRM 7M (Reasoning).
# Total VRAM footprint: ~150-200MB per agent (~2.4GB total).

EXPERTS_CONFIG = [
    {
        "name": "Archi",
        "role": "Architect",
        "background": "Expert in system design, high-level planning, and scalable architecture patterns.",
        "specialties": ["System Design", "Scalability", "Infrastructure", "Microservices"],
        "avatar_color": "#00aaff",
        "skills": [FileSkill, DocSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Devo",
        "role": "Lead Developer",
        "background": "Full-stack engineer with focus on clean code, design patterns, and rapid prototyping.",
        "specialties": ["Python", "JavaScript", "React", "Rust", "FastAPI"],
        "avatar_color": "#00ff41",
        "skills": [FileSkill, ShellSkill, CodeAnalysisSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill, TRMSkill],
    },
    {
        "name": "Seeker",
        "role": "Researcher",
        "background": "Specializes in information retrieval, documentation analysis, and knowledge synthesis.",
        "specialties": ["Web Research", "Paper Analysis", "Fact Checking", "Summarization"],
        "avatar_color": "#ff00ff",
        "skills": [WebSearchSkill, FileSkill, DocIngestionSkill, MCPToolSkill, HighQualityEmbeddingSkill, SpectralEmbeddingSkill],
    },
    {
        "name": "Logic",
        "role": "Reasoning Engine",
        "background": "Focused on complex logical deductions, mathematical proofs, and algorithm design. Uses TRM Reasoning for deep recursive loops (3-5 cycles) on every architecture task.",
        "specialties": ["Logic", "Math", "Algorithms", "Optimization", "Recursive Reasoning"],
        "avatar_color": "#ffff00",
        "skills": [FileSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill, TRMSkill],
    },
    {
        "name": "Shield",
        "role": "Security Auditor",
        "background": "Expert in cybersecurity, vulnerability assessment, penetration testing, and auditing.",
        "specialties": ["Security", "Cryptography", "Pentesting", "OWASP"],
        "avatar_color": "#ff4444",
        "skills": [FileSkill, CodeAnalysisSkill, ShellSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Flow",
        "role": "DevOps Engineer",
        "background": "Specializes in CI/CD pipelines, containerization, cloud infrastructure, and deployment.",
        "specialties": ["Docker", "Kubernetes", "Cloud Native", "GitHub Actions"],
        "avatar_color": "#00ffff",
        "skills": [FileSkill, ShellSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Vision",
        "role": "UI/UX Designer",
        "background": "Focuses on aesthetic excellence, user experience, and modern design systems.",
        "specialties": ["Design Systems", "CSS", "Figma", "Accessibility"],
        "avatar_color": "#ff8800",
        "skills": [FileSkill, DocSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Verify",
        "role": "QA Engineer",
        "background": "Dedicated to testing, bug detection, reliability engineering, and quality assurance.",
        "specialties": ["Unit Testing", "Integration Testing", "Playwright", "Pytest"],
        "avatar_color": "#88ff00",
        "skills": [FileSkill, CodeAnalysisSkill, ShellSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Orchestra",
        "role": "Swarm Manager",
        "background": "Coordinates between agents, manages subagent lifecycles, and optimizes task delegation.",
        "specialties": ["Coordination", "Resource Management", "Scheduling", "Delegation"],
        "avatar_color": "#aa00ff",
        "skills": [FileSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill, RelationshipReasoningSkill],
    },
    {
        "name": "Scribe",
        "role": "Technical Writer",
        "background": "Expert in documentation, technical writing, API docs, and clear communication.",
        "specialties": ["Markdown", "API Docs", "READMEs", "Tutorials"],
        "avatar_color": "#ffffff",
        "skills": [FileSkill, DocSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
    {
        "name": "Bridge",
        "role": "Integration Specialist",
        "background": "Specializes in MCP protocol, API bridging, webhooks, and tool interoperability.",
        "specialties": ["MCP", "REST APIs", "WebSockets", "Webhooks"],
        "avatar_color": "#ff6699",
        "skills": [FileSkill, WebSearchSkill, DocIngestionSkill, MCPToolSkill, FastEmbeddingSkill],
    },
    {
        "name": "Pulse",
        "role": "Data Analyst",
        "background": "Expert in data processing, statistical analysis, insights generation, and visualization.",
        "specialties": ["Pandas", "NumPy", "Visualization", "ML Pipelines"],
        "avatar_color": "#00ff99",
        "skills": [FileSkill, DataSkill, DocIngestionSkill, MCPToolSkill, WebSearchSkill, FastEmbeddingSkill],
    },
]


def get_expert_team() -> dict:
    team = {}
    for cfg in EXPERTS_CONFIG:
        persona = AgentPersona(
            name=cfg["name"],
            role=cfg["role"],
            background=cfg["background"],
            specialties=cfg["specialties"],
            avatar_color=cfg.get("avatar_color", "#00ff41"),
        )
        skills = [SkillClass() for SkillClass in cfg.get("skills", [])]
        agent = BaseAgent(persona, skills=skills)
        team[cfg["role"]] = agent
    return team
