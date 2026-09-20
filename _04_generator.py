# _04_generator.py
#---------------------------------------------------------------------------------
# Generiert neuen Workflow zu Projektname (siehe __current__.py)
# Prompt zu schreiben in: init/objective.md
# Der initiale Workflow landet in workflows/{id}/initial.json
#---------------------------------------------------------------------------------
from __current__ import NAME
from src.services import Ollama, N8N
from src.utils import Utils as U
from src.models import models

#---------------------------------------------------------------------------------

def generate(name):

    tpl = U.read_file(f"prompts/init/MAIN.md")
    prompt = U.orch_prompts(tpl)

    placeholders = {
        "name":         name, 
        "k2c":          N8N().map_key2cid(),
        "objective":    U.read_file(f"workflows/{name}/objective.md"),
    }
    final_prompt = U.render_template(prompt, placeholders)
    #print("final_prompt", final_prompt)
    print("NAME",NAME)
    cond = "__" not in final_prompt and "{}" not in final_prompt
    U.check(cond, "final_prompt valid")

    print("generating new n8n workflow ...")
    #func = Ollama().chat
    # ALT:
    # wf_init: dict = U.retry(func, "qwen2.5-coder", final_prompt, "json", True)

    # NEU (Direktaufruf ohne Retry-Loop-Timeout):
    wf_init = Ollama().chat(model="qwen2.5-coder", prompt=final_prompt, out="json")

    print("wf_init",wf_init)

    cond = wf_init and isinstance(wf_init, dict)
    U.check(cond, "workflow is dict")

    # --- REPARATUR / ABSICHERUNG FÜR OLLAMA ---
    # n8n verlangt zwingend ein Top-Level 'name'-Attribut
    if isinstance(wf_init, dict):
        wf_init.setdefault("name", f"Workflow_{name[:8]}")
        wf_init.setdefault("nodes", [])
        wf_init.setdefault("connections", {})
        wf_init.setdefault("settings", {})
    # ------------------------------------------

    print("dic", dict(wf_init.items()))

    saved = U.write_file(wf_init, f"workflows/{name}/initial.json")
    U.check(saved, "save workflow")
    saved = U.add_log({"system": "initial workflow json generated"}, NAME)
    U.check(saved, "add init generate to logs")

#---------------------------------------------------------------------------------

if __name__ == "__main__":
    generate(NAME)

