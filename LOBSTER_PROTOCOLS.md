# Lobster Shell Protocols

The **Lobster Shell** is the deterministic execution layer of Swarm OS. It replaces loose asynchronous tool calls with structured, typed pipelines.

## 1. LOBSTER_PIPE Action Tag

Agents can execute multi-step tool sequences using the `LOBSTER_PIPE` tag. This ensures that the output of one tool flows into the next with strict type shaping.

### Syntax

```
LOBSTER_PIPE:
{
  "name": "Pipeline Name",
  "steps": [
    {
      "tool": "tool_name",
      "args": { "param": "value" },
      "transform": "pick:id"
    },
    {
      "tool": "next_tool",
      "transform": "json"
    }
  ]
}
```

### Supported Transforms

- `pick:key`: Extracts a specific key from a JSON object or list of objects.
- `head:N`: Truncates a list to the first N items.
- `json`: Parses a string response into a JSON object for the next step.

---

## 2. ATTEMPT_SAMPLING (Quantum Superposition)

For high-complexity tasks, agents can engage in **Attempt Sampling**. This spawns parallel states (subordinate agents in isolated worktrees) to explore the solution space.

### Syntax

```
ATTEMPT_SAMPLING: <Task Description> | <Number of Attempts>
```

The orchestrator will automatically "collapse" the wavefunction by auditing all results and merging the optimal state.

---

## 3. Human-in-the-Loop Gates

Standardize your pipelines by adding `"gate": "manual"` to any step. This will pause execution until user approval is received.
