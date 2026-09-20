# src/auth_types.py
#---------------------------------------------------------------------------------
# Credential-Standard fuer n8n (dynamisch, NodeType-getrieben).
#
# WICHTIG (das war der eigentliche Bug):
#   n8n bindet Credentials NICHT ueber den Auth-Mechanismus (header/basic/oauth2),
#   sondern ueber den EXAKTEN Credential-Type-Namen, den die jeweilige Node im
#   INodeType deklariert (z.B. `openAiApi`, `slackApi`, `googleSheetsOAuth2Api`).
#   Generische Typen (httpHeaderAuth, oAuth2Api, httpBasicAuth) funktionieren NUR
#   mit der generischen HTTP-Request-Node -> fuer dedizierte Nodes sind sie wertlos.
#
# Standard:
#   .env Key  ->  N8N_CRED_<SERVICE_LABEL>
#   .env Wert ->  entweder ein roher Secret-String (Single-Secret Services)
#                 oder ein JSON-Objekt mit rohen Feldern (Multi-Field, z.B. OAuth2)
#
#   Der exakte n8n-Credential-Type wird zur Runtime vom LLM aus der offiziellen
#   n8n-NodeType-Doku hergeleitet und GEGEN das Live-Schema von n8n validiert
#   (GET /credentials/schema/{type}). Ergebnis liegt in credentials/allocations.json.
#---------------------------------------------------------------------------------

# Alles hinter diesem Prefix ist ein Node-Credential:
CRED_PREFIX = "N8N_CRED_"

# Datei, in der die (bulletproof validierten) Name<->Type Allokationen liegen.
# Enthaelt bewusst KEINE Secrets - nur die Zuordnung + die n8n Credential-ID.
ALLOCATIONS_PATH = "credentials/allocations.json"

# field_map Source-Token: "der gesamte rohe .env Wert" (Single-Secret Fall).
RAW_SOURCE = "$"

#---------------------------------------------------------------------------------
# Nur noch als bewusster Fallback fuer die GENERISCHE HTTP-Request-Node dokumentiert
# (n8n-nodes-base.httpRequest mit authentication="genericCredentialType").
# Fuer dedizierte Nodes NIEMALS verwenden.
#---------------------------------------------------------------------------------
GENERIC_HTTP_CRED_TYPES = {
    "httpHeaderAuth": {"data": ["name", "value"]},
    "httpBasicAuth":  {"data": ["user", "password"]},
    "oAuth2Api":      {"data": ["clientId", "clientSecret", "authUrl",
                                "accessTokenUrl", "scope"]},
}


def cred_label(env_key: str) -> str:
    """N8N_CRED_OPENAI -> OPENAI"""
    return env_key[len(CRED_PREFIX):] if env_key.startswith(CRED_PREFIX) else env_key


def build_data(field_map: dict, raw: str) -> dict:
    """Rekonstruiert das n8n `data`-Objekt aus dem rohen .env Wert + field_map.
    Secrets bleiben so ausschliesslich in .env und werden erst beim Upload materialisiert."""
    from json import loads, JSONDecodeError
    try:
        obj = loads(raw)
    except (JSONDecodeError, TypeError):
        obj = None
    data = {}
    for field, src in field_map.items():
        if src == RAW_SOURCE:
            data[field] = raw
        elif isinstance(obj, dict) and src in obj:
            data[field] = obj[src]
        else:
            raise ValueError(f"env value has no key '{src}' for credential field '{field}'")
    return data
