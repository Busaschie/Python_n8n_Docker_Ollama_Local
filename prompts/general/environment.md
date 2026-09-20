
# Environment
**The workflow must flawlessly function under following conditions:**
- N8N running inside a local Docker container.
- Docker Image -> N8N Version: `n8nio/n8n:latest`.
- Workflow must in each and every aspect be fully controllable via REST API from Python 3.13 (including workflow execution and debugging).
- Workflow may NOT rely on n8n UI actions, while still allowing for them via: `http://localhost:port` without limitation.
