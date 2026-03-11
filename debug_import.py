import sys
sys.path.append(".")
import time

imports = [
    "from swarm_v2.core.base_agent import AgentPersona, BaseAgent",
    "from swarm_v2.skills.file_skill import FileSkill, WebSearchSkill, CodeAnalysisSkill, DataSkill, DocSkill",
    "from swarm_v2.skills.hardened_shell_skill import HardenedShellSkill",
    "from swarm_v2.skills.doc_ingestion_skill import DocIngestionSkill",
    "from swarm_v2.skills.mcp_tool_skill import MCPToolSkill",
    "from swarm_v2.skills.embedding_skill import EmbeddingSkill, FastEmbeddingSkill, HighQualityEmbeddingSkill, SpectralEmbeddingSkill",
    "from swarm_v2.skills.trm_skill import TRMSkill",
    "from swarm_v2.skills.relationship_skill import RelationshipReasoningSkill",
    "from swarm_v2.skills.rlm_skill import RLMSkill"
]

for stmt in imports:
    print(f"Executing: {stmt}", flush=True)
    try:
        exec(stmt)
        print("OK", flush=True)
    except Exception as e:
        print(f"FAILED: {e}", flush=True)

print("ALL IMPORTS DONE.", flush=True)
