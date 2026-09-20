# _05_deploy.py
#---------------------------------------------------------------------------------
# Erstellt Workflow bei n8n zu Projektname (siehe __current__.py)
# In der n8n UI ist der Workflow dann zu sehen unter "Overview" (klick oben links)
#---------------------------------------------------------------------------------
from __current__ import NAME
from src.utils import Utils as U
from src.services import N8N
#---------------------------------------------------------------------------------


def deploy(name, update=False):
    try:
        n8n = N8N()
        master = U.read_file("workflows/master.json")

        existing_id = master.get(name, {}).get("id")

        initial = U.read_file(f"workflows/{name}/initial.json")
        prepared = n8n.failfast(initial)

        # 'id' ZWINGEND aus dem Body entfernen, da n8n diese im Body verbietet
        prepared.pop("id", None)

        # Update durchführen, wenn ID in master.json existiert
        if existing_id:
            workflow = n8n.deploy(prepared, wid=existing_id)
        else:
            workflow = n8n.deploy(prepared)

        wid = workflow.get("id") if isinstance(workflow, dict) else existing_id
        U.check(workflow and wid, "deploy workflow", wid)

        master[name]["id"] = wid
        saved = U.write_file(master, "workflows/master.json")
        U.check(saved, "save workflow id", wid)

        saved = U.add_log({"system": "workflow deployed to n8n"}, NAME)
        U.check(saved, "add deploy to logs")

    except Exception as e:
        print("deployment process failed:", e)

#---------------------------------------------------------------------------------

print("name", NAME)
if __name__ == "__main__":
    deploy(NAME)