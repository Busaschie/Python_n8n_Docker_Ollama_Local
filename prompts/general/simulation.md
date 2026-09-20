
# Simulation & Expectation
- DO NOT return the workflow buggy, broken or unfinished.
- BEFORE returning the workflow, ALWAYS perform recursive reasoning, testing and refining by:
  - comparing the workflow to best n8n practices.
  - running the result in a sandboxed environment (placeholders/simulations where needed).
  - comparing the expected results of running it to the actual resuluts of running it.
  - monitoring all relevant aspects throughout this entire process (inputs, outputs, node connections, params, credentials, documentations, success states, errors, logs, updates etc).
  - debugging any aspects that leas or may lead to errors or problems.
- LOOP UNTIL GOOD: Perform the recursive process until no uncertainties about fully frictionless functionality of the entire workflow remain.
- ONLY AFTER this recursive process is successful, add the workflow to your output.
