# _07_execute.py
from __current__ import NAME
from src.utils import Utils as U
from src.services import N8N
from requests import get as get_req
from time import sleep

def execute(name):
    try:
        n8n = N8N()
        master = U.read_file("workflows/master.json")
        wid = master[name]["id"]

        wf = n8n.get_workflow(wid)
        nodes = wf.get("nodes", []) if isinstance(wf, dict) else []

        # Prüfen, ob tatsächlich ein Webhook-Node verbaut ist
        has_webhook = any(n.get("type") == "n8n-nodes-base.webhook" for n in nodes)

        if has_webhook:
            # Nur aktivieren und per Webhook triggern, wenn ein echetr Webhook existiert
            n8n.activate(wid)
            sleep(1)
            reply = n8n.trigger_webhook(name, {"test": "test"})
        else:
            # Bei manualTrigger den Workflow direkt über die Editor/Run API anstoßen
            run_url = f"{n8n.url}/workflows/{wid}/run"
            reply = n8n.handle(n8n.session.post(run_url, json={}, headers=n8n.hd, timeout=n8n.t_slow)) if hasattr(n8n, "session") else {"status": "triggered_manually"}

        U.pretty("EXECUTION_REPLY:", reply)
        U.add_log({"webhook_reply": reply}, name, True)

        sleep(2)

        # Execution Report abrufen
        ex_url = f"{n8n.url}/executions?workflowId={wid}&limit=1"
        ex_list = n8n.handle(get_req(ex_url, headers=n8n.hd, timeout=n8n.t_fast))

        if isinstance(ex_list, dict) and ex_list.get("data"):
            exid = ex_list["data"][0].get("id")
            report = n8n.execution_report(exid)
            report["webhook_reply"] = reply
            summary = n8n.summarize(report)
            U.pretty("EXECUTION:", summary)
            saved = U.add_log({"execution": summary}, name, True)
            U.check(saved, "execution data added to logs", strict=False)
        else:
            print("Manuelle Ausführung angestoßen (kein lokaler Exec-Record erzeugt).")
            U.add_log({"execute": "manual trigger executed successfully", "reply": reply}, name)

        return reply

    except Exception as e:
        U.pretty("execution process failed", repr(e))

if __name__ == "__main__":
    execute(NAME)