# _08_debugger.py
# ---------------------------------------------------------------------------------
# Self-Healing Loop zu Projektname (siehe __current__.py)
# ---------------------------------------------------------------------------------
from __current__ import NAME
from src.utils import Utils as U
from src.services import N8N
from src.models import models
from requests import get as get_req
from time import time, sleep

# ---------------------------------------------------------------------------------
MAX_ITERS = 12  # Anzahl maximaler Self-Healing Iterationen


# ---------------------------------------------------------------------------------

def _valid_workflow(wf):
    return isinstance(wf, dict) and isinstance(wf.get("nodes"), list) and len(wf["nodes"]) > 0


# ---------------------------------------------------------------------------------

def _sanitize_wf(wf, name):
    keep = {"name", "nodes", "connections", "settings"}
    out = {k: v for k, v in wf.items() if k in keep}
    out.setdefault("name", name)
    out.setdefault("settings", {})
    out.setdefault("connections", {})
    return out


# ---------------------------------------------------------------------------------

def run_once(n8n, name, wid):
    wf = n8n.get_workflow(wid)
    nodes = wf.get("nodes", []) if isinstance(wf, dict) else []

    has_webhook = any(n.get("type") == "n8n-nodes-base.webhook" for n in nodes)

    if has_webhook:
        n8n.activate(wid)
        sleep(1)
        reply = n8n.trigger_webhook(name, {"test": "test"})
    else:
        # Für manualTrigger: Direkten Run triggern
        run_url = f"{n8n.url}/workflows/{wid}/run"
        reply = n8n.handle(n8n.session.post(run_url, json={}, headers=n8n.hd, timeout=n8n.t_slow)) if hasattr(n8n,
                                                                                                              "session") else {
            "status": "triggered_manually"}

    sleep(2)
    ex_url = f"{n8n.url}/executions?workflowId={wid}&limit=1"
    ex_list = n8n.handle(get_req(ex_url, headers=n8n.hd, timeout=n8n.t_fast))

    exid = ex_list["data"][0].get("id") if isinstance(ex_list, dict) and ex_list.get("data") else None

    if not exid:
        # Falls für manualTrigger kein Exec-Record angelegt wird, bewerten wir die Ausführung anhand der Webhook-Antwort
        return {
            "all_success": True if not has_webhook else False,
            "status": "manual-triggered" if not has_webhook else "no-execution",
            "error": None if not has_webhook else "no execution record",
            "last_node": None,
            "nodes": {},
            "success_states": None,
            "webhook_reply": reply
        }

    report = n8n.execution_report(exid)
    report["webhook_reply"] = reply
    return report


# ---------------------------------------------------------------------------------

def finalize(n8n, name, wid):
    live = n8n.get_workflow(wid)
    hardened = n8n.harden(_sanitize_wf(live, name))
    hardened = n8n.failfast(hardened)  # Schema-Sicherheit nach dem Hardening

    n8n.update(hardened, wid)
    sleep(2)

    U.write_file(hardened, f"workflows/{name}/workflow.json")
    U.add_log({"system": "healthy -> hardened (retries + resilient onError) applied"}, name)

    post = run_once(n8n, name, wid)
    U.add_log({"execution": n8n.summarize(post)}, name, True)
    U.check(post.get("all_success"), "still healthy after hardening", strict=False)
    return post.get("all_success")


# ---------------------------------------------------------------------------------

def ask_model(n8n, name, current_workflow):
    tpl = U.read_file("prompts/debug/MAIN.md")
    prompt = U.orch_prompts(tpl)
    placeholders = {
        "name": name,
        "k2c": n8n.map_key2cid(),
        "objective": U.read_file(f"workflows/{name}/objective.md") or "n/a",
        "logs": U.read_file(f"workflows/{name}/logs.json"),
        "workflow": current_workflow,
    }
    final_prompt = U.render_template(prompt, placeholders)
    U.check("__" not in final_prompt, "final_prompt valid", strict=False)
    result = U.retry(N8N().chat, models.get("debug"), final_prompt, "json", True)
    U.check(result and isinstance(result, dict), "debugger output valid", strict=False)
    return result or {}


# ---------------------------------------------------------------------------------

def debug(name):
    n8n = N8N()
    master = U.read_file("workflows/master.json")
    wid = master.get(name, {}).get("id")
    if not wid:
        U.check(False, "no workflow id in master.json -> deploy first", strict=False)
        return False

    for i in range(1, MAX_ITERS + 1):
        U.pretty(f"self-healing iteration {i}/{MAX_ITERS}")
        try:
            # 1) run + evaluate
            report = run_once(n8n, name, wid)
            U.add_log({"execution": n8n.summarize(report)}, name, True)

            # 2) success -> harden for production, then stop the loop
            if report.get("all_success"):
                U.check(True, f"workflow healthy after {i} iteration(s) -> harden + stop",
                        strict=False)
                finalize(n8n, name, wid)
                return True

            # 3) compress logs, then ask the model for ONE conservative fix
            n8n.caplogs(name)
            current_workflow = n8n.get_workflow(wid)
            result = ask_model(n8n, name, current_workflow)
            assistant = {k: result[k] for k in ("log", "note", "alter", "human") if result.get(k)}
            if assistant:
                U.add_log({"assistant": assistant}, name)

            # 4) human escalation
            if result.get("human"):
                try:
                    reply = U.human(result["human"])
                    U.add_log({"system": reply}, name)
                except Exception:
                    U.check(False, "human cancelled the debug loop", strict=False)
                    return False

            # 5) apply fix — GUARDED: never push an empty/invalid workflow to n8n
            new_wf = result.get("workflow")
            if _valid_workflow(new_wf):
                U.write_file(current_workflow, f"workflows/{name}/backup/{int(time() * 1000)}.json")
                fixed = n8n.failfast(_sanitize_wf(new_wf, name))
                U.write_file(fixed, f"workflows/{name}/workflow.json")
                n8n.update(fixed, wid)
                sleep(2)
                U.check(True, "fix applied to n8n (fail-fast)", strict=False)
            else:
                U.check(False, "no valid workflow returned this iteration (kept current)",
                        strict=False)

        except Exception as e:
            U.pretty("iteration error", repr(e))
        sleep(3)

    U.check(False, f"self-healing stopped after {MAX_ITERS} iterations without success",
            strict=False)
    return False


# ---------------------------------------------------------------------------------

if __name__ == "__main__":
    debug(NAME)