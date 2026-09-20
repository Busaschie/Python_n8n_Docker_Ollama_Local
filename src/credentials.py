# src/credentials.py
#---------------------------------------------------------------------------------
# CredentialResolver: leitet fuer jedes N8N_CRED_* Secret aus der .env den EXAKTEN
# n8n Credential-Type her (LLM + offizielle NodeType-Doku) und validiert ihn
# bulletproof gegen das LIVE-Schema der n8n Instanz (GET /credentials/schema/{type}).
#
# Ergebnis -> credentials/allocations.json  (Name<->Type Zuordnung, OHNE Secrets).
# So ist auf einen Blick sichtbar, welches .env-Secret welchem n8n-Typ/Node
# zugeordnet wurde, ohne im Terminal zu scrollen.
#---------------------------------------------------------------------------------
from json import loads, JSONDecodeError
from time import time
from src.utils import Utils as U
from src.auth_types import ALLOCATIONS_PATH, RAW_SOURCE, cred_label
from src.models import models
#---------------------------------------------------------------------------------


class CredentialResolver:

    def __init__(self, n8n, service):
        self.n8n = n8n        # N8N Instanz -> Schema-Validierung
        self.ai = service
        self._schema_cache = None

    def _get_schemas(self):
        """Holt Schemas mit Timeout und Caching, um Timeouts zu verhindern."""
        if self._schema_cache is not None:
            return self._schema_cache

        try:
            # Expliziter Timeout von 30 Sekunden für den Schema-Download
            self._schema_cache = self.n8n.get_node_types(timeout=30)
            return self._schema_cache
        except Exception as e:
            print(f"⚠️ Warnung beim Schema-Abruf: {e}")
            return {}


    #-- .env Wert analysieren -----------------------------------------------------
    def value_kind(self, raw):
        """('raw', []) fuer einen Secret-String, ('json', [keys]) fuer ein JSON-Objekt."""
        try:
            obj = loads(raw)
        except (JSONDecodeError, TypeError):
            return "raw", []
        if isinstance(obj, dict):
            return "json", list(obj.keys())
        return "raw", []

    def signature(self, raw):
        """Struktur-Fingerprint (kein Secret) -> Cache invalidiert nur bei Strukturaenderung."""
        kind, fields = self.value_kind(raw)
        return f"{kind}:{','.join(sorted(fields))}"

    #-- LLM fragen ----------------------------------------------------------------
    def _ask(self, env_key, service, kind, fields, feedback=""):
        tpl = U.read_file("prompts/creds/resolve.md")
        prompt = U.render_template(tpl, {
            "env_key":      env_key,
            "service":      service,
            "value_kind":   kind,
            "value_fields": ", ".join(fields) if fields else "single raw secret string",
        })
        if feedback:
            prompt += f"\n\n---\n# Correction required (previous answer was rejected)\n{feedback}\n"
        return self.ai.chat(models.get("creds"), prompt, "json", websearch=True)

    #-- gegen das Live-Schema von n8n validieren ----------------------------------
    def _validate(self, proposal, kind, fields):
        """returns (ok, error_msg, schema)."""
        if not isinstance(proposal, dict):
            return False, "Model output was not a JSON object.", {}
        ctype = proposal.get("n8n_credential_type")
        if not ctype:
            return False, "Missing 'n8n_credential_type'.", {}

        schema = self.n8n.get_cred_schema(ctype)
        props = (schema or {}).get("properties")
        if not props:
            return False, (f"Credential type '{ctype}' does not exist in this n8n instance "
                           f"(GET /credentials/schema/{ctype} returned no schema). "
                           f"Propose the correct, existing n8n credential type."), {}

        required = schema.get("required") or list(props.keys())
        fmap = proposal.get("field_map") or {}

        missing = [f for f in required if f not in fmap]
        if missing:
            return False, (f"Schema of '{ctype}' requires {required} "
                           f"(all fields: {list(props.keys())}). field_map is missing {missing}. "
                           f"Map every required field."), schema

        unknown = [f for f in fmap if f not in props]
        if unknown:
            return False, (f"field_map contains fields not in '{ctype}' schema "
                           f"{list(props.keys())}: {unknown}."), schema

        for f, src in fmap.items():
            if src == RAW_SOURCE:
                if kind != "raw":
                    return False, (f"Field '{f}' uses '$' (whole raw value) but the .env value "
                                   f"is a JSON object; map it to one of {fields}."), schema
            elif kind != "json" or src not in fields:
                return False, (f"Field '{f}' maps to '{src}', not a key of the .env JSON "
                               f"(available: {fields})."), schema

        if kind == "raw" and sum(1 for s in fmap.values() if s == RAW_SOURCE) > 1:
            return False, (f"The .env value is a single raw string but multiple fields map to it. "
                           f"Provide the secret as a JSON object with keys {required} in .env, "
                           f"or map only the single secret field."), schema

        return True, "", schema

    #-- ein Secret aufloesen ------------------------------------------------------
    def resolve_one(self, env_key, raw, retries=4):
        service = cred_label(env_key)
        kind, fields = self.value_kind(raw)
        feedback = ""
        for _ in range(retries):
            proposal = U.retry(self._ask, env_key, service, kind, fields, feedback, retries=2)
            ok, err, schema = self._validate(proposal, kind, fields)
            if ok:
                props = schema.get("properties", {})
                return {
                    "service":             service,
                    "env_key":             env_key,
                    "credential_name":     service,
                    "n8n_credential_type": proposal["n8n_credential_type"],
                    "node_types":          proposal.get("node_types", []),
                    "field_map":           proposal["field_map"],
                    "schema_required":     schema.get("required") or list(props.keys()),
                    "value_kind":          kind,
                    "validated":           True,
                    "reasoning":           proposal.get("reasoning", ""),
                    "signature":           self.signature(raw),
                    "resolved_ts":         int(time()),
                    "id":                  None,
                }
            print(f"↩️  {env_key}: {err}")
            feedback = err
        U.check(False, f"could not resolve credential for {env_key} (last error: {feedback})",
                strict=False)
        return None

    #-- alle Secrets aufloesen (mit deterministischem Cache) ----------------------
    def resolve_all(self, force=False):
        nenv = U.get_node_env()
        allocations = U.read_file(ALLOCATIONS_PATH) or {}
        for env_key, raw in nenv.items():
            cached = allocations.get(env_key)
            if (not force and cached and cached.get("validated")
                    and cached.get("signature") == self.signature(raw)):
                U.pretty(f"cache hit {env_key} -> {cached['n8n_credential_type']}")
                continue
            alloc = self.resolve_one(env_key, raw)
            if not alloc:
                continue
            allocations[env_key] = alloc
            U.write_file(allocations, ALLOCATIONS_PATH)
            U.pretty(f"resolved {env_key} -> {alloc['n8n_credential_type']}",
                     {"node_types": alloc["node_types"], "reasoning": alloc["reasoning"]})
        return allocations
