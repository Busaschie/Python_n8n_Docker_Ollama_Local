
# Node Credentials
- The following credentials already exist in n8n and are the ONLY ones you may use.
  Each entry is validated against the live n8n credential schema:

  __k2c__

- Each entry has: `credential_name`, `credential_type` (the exact n8n type), `id`,
  and `node_types` (the node type identifiers that consume this credential).
- Binding rule (n8n resolves credentials by TYPE, not by auth mechanism):
  - For every node that requires authentication, set its `credentials` block so the
    KEY is the exact `credential_type` and the value is `{ "id": <id>, "name": <credential_name> }`.
  - Example: `"credentials": { "openAiApi": { "id": "abc123", "name": "OPENAI" } }`
- Only build nodes whose required credential type is present in the list above, or
  nodes that need no credential at all. Do NOT invent credential ids, names or types.
- Prefer the dedicated node listed under `node_types` for a given credential. Never
  attach a generic type (`httpHeaderAuth`, `httpBasicAuth`, `oAuth2Api`) to a
  dedicated node — dedicated nodes only accept their own declared credential type.
