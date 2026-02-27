# Fix: Agents should read LOCAL files, not search web for code
with open('swarm_v2/core/llm_brain.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the CAPABILITIES section to emphasize LOCAL file reading
old_cap = '''## YOUR CAPABILITIES
- READ_CODE: Use FileSkill to read any file in the codebase
- LEARN: Use DocIngestionSkill to ingest documentation and learn new skills
- SEARCH: Use WebSearchSkill to search the web
- TOOLS: Use MCPToolSkill to call MCP microservices
- EMBED: Use EmbeddingSkill for semantic search'''

new_cap = '''## YOUR CAPABILITIES
- READ_CODE: Use FileSkill to read LOCAL files in the codebase (NOT web search!)
- LEARN: Use DocIngestionSkill to ingest LOCAL documentation and learn new skills
- SEARCH: Use WebSearchSkill ONLY for web research (not for code!)
- TOOLS: Use MCPToolSkill to call MCP microservices
- EMBED: Use EmbeddingSkill for semantic search

**IMPORTANT**: For any code in this project, use FileSkill.read_file() - NEVER search the web for code that exists locally!'''

if old_cap in content:
    content = content.replace(old_cap, new_cap)
    with open('swarm_v2/core/llm_brain.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed! Agents now know to read LOCAL files')
else:
    print('Could not find the capability section to update')
