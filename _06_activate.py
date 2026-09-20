# _06_activate.py
#---------------------------------------------------------------------------------
# Aktiviert Workflow in n8n zu Projektname (siehe __current__.py)
#---------------------------------------------------------------------------------

from __current__ import NAME
from src.utils import Utils as U
from src.services import N8N
'''
n8n = N8N()
master = U.read_file("workflows/master.json")
wid = master[NAME]["id"]

wf = n8n.get_workflow(wid)
print("--- REMOTE NODES AUF N8N ---")
for node in wf.get("nodes", []):
    print(f"Name: {node.get('name')} | Type: {node.get('type')} | typeVersion: {node.get('typeVersion')}")
'''

def activate(name):
    try:
        n8n = N8N()
        master = U.read_file("workflows/master.json")
        wid = master[name]["id"]

        wf = n8n.get_workflow(wid)
        nodes = wf.get("nodes", [])

        # Prüfen, ob automatische Trigger vorhanden sind
        auto_triggers = [
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.scheduleTrigger",
            "n8n-nodes-base.pollTrigger"
        ]
        has_auto_trigger = any(n.get("type") in auto_triggers for n in nodes)

        if not has_auto_trigger:
            print("Workflow enthält nur manuelle Trigger - keine Aktivierung erforderlich/möglich (bereit zur Ausführung).")
            U.check(True, "workflow ready (manual trigger)", strict=False)
            return True

        # Falls automatische Trigger da sind: Aktivierungs-Call durchführen
        if not wf.get("active"):
            res = n8n.activate(wid)
            if isinstance(res, dict) and res.get("active"):
                U.check(True, "workflow activated", strict=False)
                return True
            else:
                U.add_log({"activate_error": res}, NAME, True)
                return False
        else:
            print("workflow already active")
            return True

    except Exception as e:
        print(f"activation process failed: {e}")
        return False

#---------------------------------------------------------------------------------

if __name__ == "__main__":
    activate(NAME)



