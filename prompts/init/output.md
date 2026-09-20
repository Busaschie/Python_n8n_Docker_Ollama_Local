
# Your Output
**The workflow as JSON:**
- Entirely valid, syntactically precisely correct, seamlessly importable (as initial deploy) to n8n, and prettified (indent=4).
- The name of the workflow must be: "__name__".
- No Root-Level IDs: Do NOT include top-level keys like `"id"`, `"versionId"`, `"createdAt"`, or `"updatedAt"`.
- No Node-Level IDs: Do NOT assign manual `"id"` keys to individual nodes.
- Allowed Keys: Only return `name`, `nodes`, `connections`, and `settings`. 
- Nested double quotes must be properly escaped to comply with n8n JSON syntax:
  - Example: `"jsonProperty": "{{$node[\"OpenAI Message 2\"].json[\"outputText\"]}}"`
- Always set: `"settings": {empty object}`
**Strict Output:**
- Never add any info beyond the json workflow (no comments, no metainfo etc).
- Only return the strict json as required.
