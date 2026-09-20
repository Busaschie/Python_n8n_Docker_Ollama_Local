# src/services.py
#---------------------------------------------------------------------------------
# Klassen für API Calls
#---------------------------------------------------------------------------------
import re, os, httpx
from requests import (
    post as post_req, put as put_req, get as get_req, Response as Response
)
from src.context import N8N_URL, OPENAI_API_KEY, GROQ_API_KEY, N8N_API_KEY, USER, PSWD, AUTH
#from openai import OpenAI
from openai import OpenAI as OpenAIClient
#from groq import Groq as GroqClient
from json import loads
from src.utils import Utils as U
from src.auth_types import ALLOCATIONS_PATH, build_data
from copy import deepcopy
from time import time, sleep
from json import dumps
from src.models import models
#---------------------------------------------------------------------------------
OLLAMA_HOST_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
OLLAMA_DOCKER_URL = os.getenv("OLLAMA_DOCKER_URL", "http://host.docker.internal:11434")

class Ollama:

    def __init__(self):
        # Timeout direkt im Client verankern, um unendliche Hänger zu vermeiden
        http_client = httpx.Client(
            trust_env=False,
            timeout=httpx.Timeout(
                connect=30.0,
                read=300.0,
                write=30.0,
                pool=30.0
            )
        )

        # Hier explizit self.client zuweisen:
        self.client = OpenAIClient(
            base_url="http://127.0.0.1:11434/v1",
            api_key="ollama",
            http_client=http_client
        )

    def get_credential_schema(self):
        return {
            "name": "Ollama account",
            "type": "ollamaApi",
            "data": {
                "baseUrl": "OLLAMA_BASE_URL",
                "apiKey": "OLLAMA_API_KEY"
            }
        }

    def chat(self, model="qwen2.5-coder", prompt="", out="", websearch=False):
        messages = []

        if out == "json":
            messages.append({
                "role": "system",
                "content": "You are a JSON-only generator. Output ONLY a valid raw JSON object. Do not wrap in markdown or add explanations."
            })

        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,  # Standardmäßig auf dein lokales qwen2.5-coder gesetzt
            "messages": messages,
            "temperature": 0.1,
        }

        if out == "json":
            kwargs["response_format"] = {"type": "json_object"}

        completion = self.client.chat.completions.create(**kwargs)
        res = completion.choices[0].message.content or ""

        if out == "json":
            # Robuste JSON-Extraktion
            res_clean = re.sub(r"^```(?:json)?\s*", "", res.strip(), flags=re.MULTILINE)
            res_clean = re.sub(r"\s*```$", "", res_clean, flags=re.MULTILINE).strip()

            match = re.search(r"\{.*\}", res_clean, re.DOTALL)
            if match:
                res_clean = match.group(0)

            try:
                return loads(res_clean)
            except Exception as e:
                print(f"❌ JSON Parse Error mit Ollama Modell {model}:\n{res}")
                raise e

        return res


class N8N:

    def __init__(self):
        self.url = f"{N8N_URL}/api/v1"
        self.auth = (USER, PSWD) if AUTH else None
        self.hd = {"X-N8N-API-KEY": N8N_API_KEY}
        self.webhook = "webhook"
        self.testhook = "webhook-test"
        self.t_fast = (10, 60)
        self.t_hook = (5, 180)

    def set_new_cred(self, s):
        url = f"{self.url}/credentials"
        return self.handle(post_req(url, json=s, headers=self.hd, timeout=self.t_fast))

    def get_cred_schema(self, ctype):
        url = f"{self.url}/credentials/schema/{ctype}"
        res = self.handle(get_req(url, headers=self.hd, timeout=self.t_fast))
        return res if isinstance(res, dict) and res.get("properties") else {}

    def existing_cred_id(self, name, ctype):
        try:
            res = self.get_creds()
            data = res.get("data", []) if isinstance(res, dict) else []
        except Exception:
            return None
        for c in data:
            if c.get("name") == name and c.get("type") == ctype:
                return c.get("id")
        return None

    def live_cred_index(self):
        try:
            res = self.get_creds()
            data = res.get("data", []) if isinstance(res, dict) else []
        except Exception:
            data = []
        return {
            "ids":   {c.get("id") for c in data},
            "by_nt": {(c.get("name"), c.get("type")): c.get("id") for c in data},
        }

    def sync_creds(self, allocations):
        nenv = U.get_node_env()
        live = self.live_cred_index()
        failed = []
        for env_key, a in allocations.items():
            raw = nenv.get(env_key)
            if raw is None:
                print(f"{env_key}: not present in .env anymore")
                failed.append(env_key)
                continue
            try:
                data = build_data(a["field_map"], raw)
            except Exception as e:
                print(f"{env_key}: {e}")
                failed.append(env_key)
                continue
            name, ctype = a["credential_name"], a["n8n_credential_type"]
            cid = a.get("id")
            if cid and cid not in live["ids"]:
                cid = None
            if not cid:
                cid = live["by_nt"].get((name, ctype))
            if not cid:
                res = self.set_new_cred({"name": name, "type": ctype, "data": data})
                cid = res.get("id") if isinstance(res, dict) else None
            if not cid:
                failed.append(env_key); continue
            a["id"] = cid
        U.write_file(allocations, ALLOCATIONS_PATH)
        return failed

    def map_key2cid(self):
        allocations = U.read_file(ALLOCATIONS_PATH) or {}
        out = [{
            "credential_name": a["credential_name"],
            "credential_type": a["n8n_credential_type"],
            "id":              a["id"],
            "node_types":      a.get("node_types", []),
        } for a in allocations.values() if a.get("id")]
        return dumps(out, indent=2, ensure_ascii=False)

    def get_creds(self):
        url = f"{self.url}/credentials"
        return self.handle(get_req(url, headers=self.hd, timeout=self.t_fast))

    # Trigger-Nodes brauchen kein Retry/Error-Handling
    _TRIGGER_TYPES = ("n8n-nodes-base.webhook", "n8n-nodes-base.manualTrigger",
                      "n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.cron",
                      "n8n-nodes-base.errorTrigger")

    def failfast(self, workflow: dict) -> dict:
        if not isinstance(workflow, dict):
            return workflow

        # Top-Level Absicherung
        workflow.setdefault("name", "Generated Workflow")
        workflow.setdefault("nodes", [])
        workflow.setdefault("connections", {})
        workflow.setdefault("settings", {})
        workflow["settings"]["saveManualExecutions"] = True
        workflow["description"] = workflow.get("description") if isinstance(workflow.get("description"), str) else ""

        # Whitelist aller von der n8n API erlaubten Eigenschaften auf Node-Ebene
        ALLOWED_NODE_KEYS = {
            "id",
            "name",
            "type",
            "typeVersion",
            "position",
            "parameters",
            "credentials",
            "disabled",
            "notes",
            "notesInFlow",
            "retryOnFail",
            "maxTries",
            "waitBetweenTries",
            "alwaysOutputData",
            "executeOnce",
            "continueOnFail",
        }

        nodes = workflow.get("nodes", [])
        clean_nodes = []
        has_trigger = False

        for node in nodes:
            if not isinstance(node, dict):
                continue

            # 1. Alle unerlaubten Zusatz-Keys filtern
            node = {k: v for k, v in node.items() if k in ALLOWED_NODE_KEYS}

            # Defaults absichern
            node.setdefault("parameters", {})
            node.setdefault("position", [250, 300])

            # 2. Trigger Identifikation & Korrektur
            if node.get("type") in ["n8n-nodes-base.start", "n8n-nodes-base.manualTrigger"]:
                node["type"] = "n8n-nodes-base.manualTrigger"
                node["typeVersion"] = 1
                has_trigger = True

            # 3. Function Nodes auf Code Nodes mappen
            elif node.get("type") in ["n8n-nodes-base.function", "n8n-nodes-base.code"]:
                node["type"] = "n8n-nodes-base.code"
                node["typeVersion"] = 2

            clean_nodes.append(node)

        # 4. Sicherheitsnetz: Falls Ollama gar keinen Trigger definiert hat
        if not has_trigger and clean_nodes:
            clean_nodes[0]["type"] = "n8n-nodes-base.manualTrigger"
            clean_nodes[0]["typeVersion"] = 1
            clean_nodes[0]["parameters"] = {}

        workflow["nodes"] = clean_nodes

        # 5. Connections-Struktur korrigieren (Expected array, received object)
        clean_connections = {}
        connections = workflow.get("connections", {})
        if isinstance(connections, dict):
            for source_node, conn_type_dict in connections.items():
                if not isinstance(conn_type_dict, dict):
                    continue
                clean_connections[source_node] = {}
                for conn_type, outputs in conn_type_dict.items():
                    if not isinstance(outputs, list):
                        continue

                    fixed_outputs = []
                    for item in outputs:
                        # Falls LLM ein Objekt statt eines Verschachtelten Arrays geliefert hat:
                        if isinstance(item, dict):
                            fixed_outputs.append([item])
                        elif isinstance(item, list):
                            fixed_outputs.append(item)

                    clean_connections[source_node][conn_type] = fixed_outputs

        workflow["connections"] = clean_connections
        return workflow

    def harden(self, workflow):
        """PRODUKTIONS-Modus (erst NACH erfolgreicher Validierung): Retries gegen transiente
        Fehler + resilientes onError. Nutzt den GUELTIGEN n8n-Wert 'continueRegularOutput'
        (das bisherige 'continue' ist KEIN gueltiger Wert -> wurde von n8n ignoriert).
        Ueberschreibt bewusst (flippt failfast -> resilient)."""
        wf = deepcopy(workflow)
        for node in wf.get("nodes", []):
            if node.get("type") in self._TRIGGER_TYPES:
                continue
            node["retryOnFail"] = True
            node["maxTries"] = 2
            node["waitBetweenTries"] = 2000
            node["onError"] = "continueRegularOutput"   # oder "stopWorkflow" fuer fail-clean
            node["alwaysOutputData"] = True
        return wf

    def deploy(self, json_data, wid=None):
        # 'id' immer aus dem Payload entfernen (n8n lehnt id im Body ab)
        if isinstance(json_data, dict):
            json_data.pop("id", None)

        if wid:
            # Update eines bestehenden Workflows via PUT
            url = f"{self.url}/workflows/{wid}"
            wf = self.handle(put_req(url, json=json_data, headers=self.hd, timeout=self.t_fast))
        else:
            # Anlegen eines neuen Workflows via POST
            url = f"{self.url}/workflows"
            wf = self.handle(post_req(url, json=json_data, headers=self.hd, timeout=self.t_fast))

        return self.clean(wf)

    def update(self, json, wid):
        url = f"{self.url}/workflows/{wid}"
        wf = self.handle(put_req(url, json=json, headers=self.hd, timeout=self.t_fast))
        return self.clean(wf)

    def activate(self, wid):
        # Der Endpoint /workflows/{wid}/activate schaltet den Workflow frei.
        # Er verlangt ein leeres Dict {} im Body, da 'active' im PUT-Payload read-only ist.
        url = f"{self.url}/workflows/{wid}/activate"
        return self.handle(post_req(url, json={}, headers=self.hd, timeout=self.t_fast))

    '''def activate(self, wid):
        # 1. Den aktuellen Workflow von n8n abrufen
        wf = self.get_workflow(wid)
        if not isinstance(wf, dict):
            return wf

        # 2. Schema und Trigger über failfast absichern
        wf = self.failfast(wf)

        # 3. Nur die explizit von n8n erlaubten Felder für das PUT-Update behalten
        # Schreibgeschützte Server-Metadaten (createdAt, updatedAt, versionId, tags, etc.) entfernen
        allowed_keys = {"name", "nodes", "connections", "settings", "staticData"}
        payload = {k: v for k, v in wf.items() if k in allowed_keys}

        # Status auf active setzen und description als String absichern
        payload["active"] = True
        payload["description"] = wf.get("description") if isinstance(wf.get("description"), str) else ""

        # 4. Update an /workflows/{wid} senden
        url = f"{self.url}/workflows/{wid}"
        return self.handle(put_req(url, json=payload, headers=self.hd, timeout=self.t_fast))'''

    def get_workflow(self, wid):
        url = f"{self.url}/workflows/{wid}"
        wf = self.handle(get_req(url, headers=self.hd, timeout=self.t_fast))
        return self.clean(wf)

    def trigger_webhook(self, name, payload, test=False):
        url = f"{N8N_URL}/{self.hook(test)}/{name}"
        return self.handle(post_req(url, json=payload, auth=self.auth, timeout=self.t_hook))

    def summarize(self, report):
        """Kompakter, loggbarer Auszug eines execution_report -> behaelt die FEHLER.
        Gemeinsam genutzt von _07_execute und _08_debugger."""
        failed = {n: nd["error"] for n, nd in report.get("nodes", {}).items() if nd.get("error")}
        return {
            "status":         report.get("status"),
            "error":          report.get("error"),
            "error_node":     report.get("error_node"),
            "last_node":      report.get("last_node"),
            "failed_nodes":   failed or None,
            "success_states": report.get("success_states"),
            "reply":          report.get("webhook_reply"),
        }

    def clean(self, workflow):
        wf = deepcopy(workflow)
        k = ("workflowPublishHistory", "shared", "activeVersion", "pinData", "meta", "staticData")
        for r in k: wf.pop(r, None)
        return wf

    def caplogs(self, wf_name):
        prompt = U.read_file("prompts/caplogs/MAIN.md")
        logs = U.read_file(f"workflows/{wf_name}/logs.json")
        prompt = prompt.replace("__logs__", str(logs))

        # Aufruf über deine lokale Ollama-Klasse
        capped = U.retry(Ollama().chat, models.get("caplogs", "qwen2.5-coder"), prompt, "json", False, retries=5)

        U.check(capped and isinstance(capped, dict), "output not valid")
        U.write_file(capped, f"workflows/{wf_name}/logs.json")
        return True

    def execute(self, wid, obj):
        url = f"{self.url}/workflows/{wid}/execute"
        res = self.handle(post_req(url, json={"inputData": obj}, headers=self.hd, timeout=self.t_hook))
        try: return int(res.get("id"))
        except: return None

    def get_ex_data(self, exid, full_data = True):
        p = {"includeData": "true"} if full_data else {}
        url = f"{self.url}/executions/{exid}"
        return self.handle(get_req(url, headers=self.hd, params=p, timeout=self.t_fast))

    def hook(self, test): 
        return "webhook-test" if test else "webhook"

    def handle(self, res):
        if not res.ok: 
            print(f"{res.status_code}: {res.text}") 
        try: return res.json()
        except: return res.text.strip()

    def _is_terminal(self, ex):
        """Execution ist fertig (Erfolg ODER Fehler), sobald sie gestoppt hat.
        WICHTIG: 'finished' ist nur bei ERFOLG true; ein hart gescheiterter Run hat
        finished=false aber stoppedAt gesetzt -> sonst pollt der Report ins Timeout und
        meldet faelschlich 'timeout' statt des echten Node-Fehlers."""
        if not isinstance(ex, dict): return False
        if ex.get("waitTill"): return False                       # auf Wait-Node pausiert
        return bool(ex.get("finished") or ex.get("stoppedAt")
                    or ex.get("status") in ("success", "error", "crashed", "canceled", "failed"))

    def _err_text(self, err):
        """Aussagekraeftige Meldung aus einem n8n Error-Objekt (message + description)."""
        if not isinstance(err, dict): return err or None
        msg = (err.get("message") or "").strip()
        desc = (err.get("description") or "").strip()
        if desc and desc.lower() not in msg.lower():
            return f"{msg} — {desc}" if msg else desc
        return msg or None

    def execution_report(self, exid, t=180):
        """Pollt bis die Execution STOPPT (nicht nur 'finished') und liefert einen reichen
        Report inkl. echter Fehler (pro Node + top-level). Der Timeout-Zweig greift nur
        noch bei einem ECHTEN Hang, nicht bei einem schnellen Node-Fehler."""
        s = time()
        while time() - s < t:
            ex = self.get_ex_data(exid, True)
            if self._is_terminal(ex):
                return self._parse_execution(ex)
            sleep(1)
        return {"finished": False, "status": "no-stop",
                "error": f"execution {exid} did not stop within {t}s (genuine hang or Wait "
                         f"node — NOT a masked node error)",
                "error_node": None, "last_node": None, "nodes": {},
                "success_states": None, "all_success": False}

    def _parse_execution(self, ex):
        rd = ex.get("data", {}).get("resultData", {})
        top_err = rd.get("error")
        nodes = {}
        for n, runs in (rd.get("runData") or {}).items():
            try: r0 = runs[0]
            except Exception: continue
            try: out = [i.get("json") for i in r0["data"]["main"][0]]
            except Exception: out = None
            nodes[n] = {"output": out, "error": self._err_text(r0.get("error"))}
        # Erfolg zuerst ueber summary_node-States, sonst Fallback
        states, all_ok = None, False
        sn = (nodes.get("summary_node") or {}).get("output")
        if isinstance(sn, list) and sn and isinstance(sn[0], dict):
            states = sn[0].get("summary")
        if isinstance(states, dict) and states:
            all_ok = all(isinstance(v, dict) and v.get("success") for v in states.values())
        else:
            all_ok = bool(ex.get("finished")) and not top_err and \
                     all(not nd["error"] for nd in nodes.values())
        # den Node, der den Abbruch verursacht hat (falls n8n ihn nennt)
        en = top_err.get("node") if isinstance(top_err, dict) else None
        error_node = en.get("name") if isinstance(en, dict) else (en if isinstance(en, str) else None)
        return {
            "finished":       bool(ex.get("finished")),
            "status":         ex.get("status") or ("error" if top_err else
                                                   ("success" if ex.get("finished") else "stopped")),
            "error":          self._err_text(top_err),
            "error_node":     error_node,
            "last_node":      rd.get("lastNodeExecuted"),
            "nodes":          nodes,
            "success_states": states,
            "all_success":    all_ok,
        }









