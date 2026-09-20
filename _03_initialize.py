# _03_initialize.py
#---------------------------------------------------------------------------------
# Init neues Workflow Projekt im 'workflows' Ordner, inkl. Projektname (uuid)
# Nach dem Ausführen den Projektnamen (uuid) in __current__.py eintragen
#---------------------------------------------------------------------------------
from src.utils import Utils as U
from uuid import uuid4
#---------------------------------------------------------------------------------

def new_project():

    name   = str(uuid4())
    print("uuid", name)

    obj    = U.read_file("prompts/init/objective.md")
    p_obj  = U.write_file(obj, f"workflows/{name}/objective.md")

    p_ini  = U.write_file({}, f"workflows/{name}/initial.json")
    p_logs = U.write_file({}, f"workflows/{name}/logs.json")
    p_wf   = U.write_file({}, f"workflows/{name}/workflow.json")

    mast   = U.read_file("workflows/master.json")
    mast[name] = {"id": None, "last_working_ts": None}
    p_mast = U.write_file(mast, "workflows/master.json")

    U.check(all((p_obj, p_ini, p_logs, p_wf, p_mast)), "project initialized")
    U.pretty("ℹ️  Define what the workflow should in: ", p_obj)

#---------------------------------------------------------------------------------

if __name__ == "__main__":
    new_project()
