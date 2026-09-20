# src/utils.py
#---------------------------------------------------------------------------------
# Klasse für Helper Functions
#---------------------------------------------------------------------------------
from src.context import ROOT
from json import load, dump, dumps
from time import time, sleep
from os import environ
from re import findall
from src.auth_types import CRED_PREFIX
#---------------------------------------------------------------------------------

class Utils:

    @staticmethod
    def read_file(path: str):
        p = ROOT / str(path)
        if not p.exists(): return {}
        with open(p, "r", encoding="utf-8") as f:
            return load(f) if str(path).endswith(".json") else f.read()

    @staticmethod
    def write_file(obj, path: str):
        p = ROOT / str(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            if str(path).endswith(".json"): dump(obj, f, ensure_ascii=False, indent=4)
            else: f.write(obj)
            return path

    @staticmethod
    def file_exists(path: str) -> bool:
        return (ROOT / path).exists()

    @staticmethod
    def render_template(tpl: str, ctx: dict = None) -> str:
        ctx = ctx or {}
        for k, v in ctx.items(): 
            tpl = tpl.replace(f"__{k}__", str(v))
        return tpl

    @staticmethod
    def pretty(title="", obj=None):
        print("-"*100)
        if title: print(f"{title}")
        if obj: print(dumps(obj, indent=2, ensure_ascii=False))
        return True

    @staticmethod
    def get_node_env():
        # Alle .env Keys, die ein n8n Node-Credential beschreiben: N8N_CRED_<LABEL>
        return {k: v for k, v in environ.items() if k.startswith(CRED_PREFIX)}

    @staticmethod
    def read_logs(path): 
        return Utils.read_file(path)

    @staticmethod
    def check(cond, msg="", obj="", strict=True):
        if cond: return Utils.pretty(f"✅ {msg}: ", obj)
        else: Utils.pretty(f"❌ {msg}: ", obj)
        if strict: raise Exception("⚠️ -> process ended without success")
        else: return False

    @staticmethod
    def retry(func, /, *args, retries=3, pause=2, spread=2, **kwargs):
        while retries > 0:
            retries -= 1
            try:
                res = func(*args, **kwargs)
                if not res: raise ValueError(f"empty: {res}")
                return res
            except Exception as e:
                print(e); sleep(pause)
                pause *= spread

    @staticmethod
    def human(msg):
        opt = ""; send = ""
        Utils.pretty("👤 Human action required! Read the model report: ", msg)
        while opt.upper() not in ("C", "R"):
            print("-"*100); opt = input("👤 (C)ancel debug-loop? | (R)eply to model?: ")
        if opt == "R": 
            print("-"*100) 
            while send.upper() not in ("C", "S"):
                reply = input("👤 Type your reply to the model: ")
                if len(reply) <= 50: 
                    print("-"*100) 
                    print("⁉️ Type something useful! (fucking ape) 🤌")
                    continue
                print("-"*100); print("👤 Your reply is: ", reply)
                print("-"*100); send = input("👤 (S)end your reply or (C)ancel the debug-loop: ")
            if send == "S": return reply
        print("-"*100)
        raise RuntimeError("⚠️ debug-loop cancelled")

    @staticmethod
    def orch_prompts(tpl):
        for p in findall(r"__(.*?)__", tpl):
            prompt = Utils.read_file(f"prompts/{p}.md")
            tpl = tpl.replace(f"__{p}__", str(prompt))
        return tpl

    @staticmethod
    def add_log(d, wf_name, dumpstr=False): 
        if dumpstr: d = {k: dumps(v, default=str) for k,v in d.items()}
        logs = Utils.read_file(f"workflows/{wf_name}/logs.json")
        logs[int(time()*1000)] = d
        saved = Utils.write_file(logs, f"workflows/{wf_name}/logs.json")
        Utils.check(saved, f"{d.keys()}: added to logs", strict=False)
        return saved or False
    
