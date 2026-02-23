# Mission: System Self-Diagnostic & Gap Analysis

## Objective

Perform a comprehensive self-check of the TRM Swarm V2 to identify operational gaps, latent bugs, and architectural recommendations. The system must demonstrate cognitive accuracy, appropriate tool leverage, and strict adherence to negative constraints (no-write-unless-asked).

## Success Criteria

1. **Cognitive Reliability**: Correct responses to simple factual/logical queries.
2. **Tool Fluency**: Successful invocation of synthesized MCP tools (specifically Weather & GitHub) when intent is clear.
3. **Constraint Adherence**: Analysis must be performed in-memory and returned as text. **Zero** new artifacts should be generated during analysis-only tasks.
4. **Gap Identification**: A specific list of system limitations discovered during the run.

## Test Tier 1: Simple Cog-Check

* **Task**: "Explain the primary difference between a Sub-Agent and an Expert in this swarm."
* **Target Result**: Accurate retrieval of swarm hierarchy logic.

## Test Tier 2: Tool Integration

* **Task**: "Fetch the current weather in Winston-Salem and Kernersville."
* **Target Result**: Successful hit on port 9110 via `MCPToolSkill`.

## Test Tier 3: Analysis & Negative Constraint

* **Task**: "Review the file `swarm_v2/core/base_agent.py`. Identify one potential memory leak or performance bottleneck in the `process_task` method. Provide the recommendation as a text response. **DO NOT WRITE TO ANY FILES OR CREATE NEW ARTIFACTS.**"
* **Target Result**: High-quality code analysis without any new `.py` or `.md` files appearing in `swarm_v2_artifacts`.

## Reporting

Upon completion, the system must generate a recommendation report (this IS an allowed file creation) summarizing the findings.
