
# Template Research
**Perform Websearch to find the most suitable template for the main objective:**
- 1) Use following links with dynamic query parameters to find 15 good n8n templates, highly relevant for our main objective:
    - a) Source: `https://n8n.io/workflows/?q={keyword+you+search}`
    - b) Source: `https://n8ntemplates.me/templates?search={keyword+you+search}`
- 2) Then pick the 5 templates whose description matches closest with our main objective.
- 3) Then the template id of all 5 templates, from their template url structures like this: 
    - a) Source: `https://n8n.io/workflows/{id}-some-template-name/`
    - b) Source: `https://n8ntemplates.me/templates/some-template-name-{id}`
- 4) Then use follwing url to directly retrieve the JSON workflow of all these 5 template ids: 
    - `https://api.n8n.io/templates/workflows/{id}`
- 5) Analyze each json workflow for matching our main objective, architecture principles and general best n8n practises.
- 6) Extract the the most matching parts/principles and apply them (where suitable) to developing out workflow.
