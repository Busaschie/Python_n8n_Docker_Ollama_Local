# _02_add_creds.py
#---------------------------------------------------------------------------------
from src.services import N8N, Ollama
from src.credentials import CredentialResolver
from src.utils import Utils as U
from src.auth_types import ALLOCATIONS_PATH
#---------------------------------------------------------------------------------

def add_creds(force=False):

    U.pretty("resolving credentials from .env against n8n NodeType schemas ...")
    n8n = N8N()
    resolver = CredentialResolver(n8n, Ollama())

    allocations = resolver.resolve_all(force=force)
    U.check(allocations, "credentials resolved + validated", ALLOCATIONS_PATH)

    U.pretty("uploading credentials to n8n ...")
    left = n8n.sync_creds(allocations)
    U.check(not left, "all credentials added to n8n", left)

#---------------------------------------------------------------------------------

if __name__ == "__main__":
    add_creds()

#---------------------------------------------------------------------------------
# Danach sind Credentials auch in n8n auffindbar in n8n UI:
# - oben links "Plus" Symbol -> "Credential", ODER
# - oben Links "Overview" -> Tab "Credentials"
#---------------------------------------------------------------------------------
