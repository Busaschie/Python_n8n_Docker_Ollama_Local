
# Architecture

### Nodes
- To validate and apply latest stable typeVersion for n8n json workflow schema for each of the involved node types, you perform lightning-fast websearch in the official n8n docs, to retrieve:
  - 1) only the links of the relevant node folders at: `https://github.com/n8n-io/n8n/tree/master/packages/nodes-base/nodes`,
  - 2) within the collected links, inside the `.node.ts` files, only the data within the `INodeType` class,
  - 3) extract the fully up-to-date and strictly correct stucture for the relevant nodes as json.
- Every node must have an explicitly defined `operation` and `resource` according to the latest n8n `INodeType` specs. 
- Each node MUST have a unique node name, using snake_casing as strict name convention.

### Summary Node
- One extra node with the exact name `summary_node` must be implemented.
- The `summary_node` should receive the final success state of every node.
- The `summary_node` should store the success states as json in following structure:
  - keys: specific unique node name (as defined in the workflow json),
  - values: {"success": bool (init state must be set to false upon every execution), "reason": string of max. 512 chars (empty on success)}.
- "success" may only be set True, if node has truly and fully succeded all of it's tasks (technically and individually).

### Node Connections
- If a node requires a sub-node (e.g. Model, Memory, Tool), then create it and connect it to the correct input on the parent node.
- If a node type belongs to `@n8n/n8n-nodes-langchain`, it never stands alone, but always needs a Provider/Model node.
- In each operational node set `"onError": "stopWorkflow"` and `"alwaysOutputData": true`.
  Fail fast so any error surfaces immediately and unambiguously while the workflow is
  being built/debugged. NEVER use `"continue"` — it is not a valid n8n value and is
  ignored. (Valid values are `stopWorkflow`, `continueRegularOutput`, `continueErrorOutput`.)
  Production resilience is applied automatically by the harness AFTER validation.
- Always research and ensure the correct input/output type structures (strict Parser Node may be required as interface).
- Where input/output type structures should frequently produce significant errors, you may apply principles of **Postel's Law**, **Loose Coupling**, **Laxity** & **Context-Passing** for dynamic input/output handling, e.g. by custom parsing of text via LLM node as interface.

### Retries & Timeouts
- Do NOT add retry settings (`retryOnFail`/`maxTries`/`waitBetweenTries`) at generation
  time. While the workflow is being built and self-healed it must FAIL FAST so the real
  error surfaces immediately; retries only hide and slow down the true cause. The harness
  injects retries + resilient error handling automatically once the workflow is validated
  as healthy.
- Set per-node timeouts ONLY where the specific node actually supports one (e.g. the
  HTTP Request node's `options.timeout` in ms). Do not invent a timeout field on nodes
  whose `INodeType` has none.
- Overall run duration is bounded server-side by the container's `EXECUTIONS_TIMEOUT`.

### Logging
- Every node shall add logs to execution objects, providing all critical and helpful debugging information to the execution logs.

### Webhook Specs
- If there is a webhook node, then do NOT use a "Respond to Webhook" node.
- Webhook parameters must be explicitly set to:
  - `"httpMethod": "POST",`
  - `"responseMode": "lastNode"`
  - `"path": "__name__"` 

### AI Nodes
- Select the most suitable, most cost-effective model of the required provider without compromising on quality (get up-to-date by websearch).
- Rely on the `@n8n/n8n-nodes-langchain.agent` nodeType standard (if applicable for the node).
- **Pin the exact model id first** (the precise model-id string, never a family or "similar" model). EVERY parameter decision below is judged against THAT one model id only — never a model family, a sibling model, or a general assumption.
- **Default-first / minimal params:** set ONLY the parameters strictly required to run the node (i.e. the model id and the input/messages). OMIT every optional tuning parameter (e.g. `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, and token-limit fields) so the model applies its own defaults. A parameter you never set can never be rejected.
- **Opt-in only with proof:** add an optional parameter ONLY IF (1) the objective genuinely requires it, AND (2) the provider's API reference documents that THIS exact model id accepts that parameter AND the specific value you set. If support or the valid range is uncertain, OMIT it — never guess.
- **Never restate a default:** do not set a parameter to (what you believe is) its default value. Redundantly declaring defaults adds risk with zero benefit — e.g. `temperature: 0` breaks models that accept only the default `temperature` (1).
- **Respect model-class constraints for the pinned model:** some current models accept only the default `temperature` (so do not set it at all), some require `max_completion_tokens` instead of `max_tokens`, and reasoning-class models may reject sampling params entirely. Confirm per the exact model id; when in doubt, leave it unset.
- **Node/model compatibility:** if the chosen node forces a parameter the pinned model would reject (e.g. a chat-model node that always sends a non-default `temperature`), then either omit that option or pick a model id that the node's parameters are compatible with — do not ship a known-invalid combination.
- Scope any websearch to the pinned model id's official API reference, only to confirm the exact valid parameter names and value ranges before setting them.

### Sticky Nodes
- Every Node should contain suitable information about its purpose and functionality.
- Sticky nodes should have friendly colors and be written very pragmatic and concise (every word must earn it's place).