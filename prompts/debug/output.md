
# Your Output
**JSON structure containing strictly following keys at top-level:**
- `"workflow": the full debugged n8n workflow.json`: 
    - Name of workflow must be: "__name__".
    - Must be entirely valid, syntactically precisely correct, seamlessly importable to n8n, and prettified (indent=4). 
    - Any nested double quotes must be properly escaped to comply with n8n JSON syntax, such as `"jsonProperty": "{{$node[\"OpenAI Message 2\"].json[\"outputText\"]}}"`. 
- `"log": string`: Short description about your debugging approach.
- `"note": string`: Short note you write to yourself for next iteration.
- `"alter": string`: Alternative approaches to solve the problem.
- `"human": string`: Keep empty, unless logs reveal that eight different debugging attempts on the same issue failed. Else, if you are fully convinced that only a human can solve the issue, then provide step-by-step instructions for the human to solve it.
**Strict Output:**
- Neither add any other top-level keys nor any other type for their values.
- Never add any info beyond the described json (no comments, no metainfo etc).
- Only return the strict json as required.
