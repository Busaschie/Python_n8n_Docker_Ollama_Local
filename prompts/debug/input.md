
# Analyze & Evaluate
- Main Objective of workflow (original prompt): "__objective__".
- Current `workflow.json` (to be bugfixed): "__workflow__".
- Identify current issues from the logs and pick most critical one to address in current iteration.
- Logs & bugfixing history (compressed): "__logs__".
- Only conservative changes, to address the only issue cluster related to one specific problem. 
- No changes to aspects that are not related to the issue or not identified as issue.
- Avoid larger changes, unless logs reveal that current issue has not been solved after five different debugging attempts.
- Take into account entire history, to avoid repeating identical debugging attempts.
- In the latest `execution` log, treat `last_node` and any `failed_nodes` entry as the
  most probable source of error; the concrete error text is in `error`/`failed_nodes`.
- **How to read the logs:**
    - Structure: timestamp: {log_type: {log_content}}.
    - log_type: "execution" -> results from n8n upon executing the workflow, with fields:
        - `status`: overall run status (e.g. success / error / timeout).
        - `error`: top-level execution error message (null if none).
        - `last_node`: name of the last node n8n executed (often where it broke).
        - `failed_nodes`: {node_name: error_message} for every node that errored (null if none).
        - `success_states`: the summary_node success map {node: {success, reason}} (null if absent).
        - `reply`: the actual HTTP reply returned to the initial webhook call.
    - log_type: "assistant" -> your relevant previous outputs per debugging step.
    - log_type: "system"    -> my manual prompt in case human action was required.
