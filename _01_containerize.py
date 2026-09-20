# _01_containerize.py
#---------------------------------------------------------------------------------
# Erstellt Docker Image und Container
# Ein Image kann etwaige Workflows verwalten
#---------------------------------------------------------------------------------
import subprocess
from src.context import PORT, N8N_URL
from time import sleep, time
from requests import get as get_req
#---------------------------------------------------------------------------------

def wait_for_n8n(url, timeout=60):
    start = time()
    while time() - start < timeout:
        try:
            r = get_req(f"{url}/health", timeout=3)
            if r.status_code == 200: return True
        except Exception:
            pass
        sleep(1)
    raise TimeoutError("n8n container did not start in time")

#---------------------------------------------------------------------------------

def docker_build_and_run_test():
    GREEN = "\033[92m"
    RESET = "\033[0m"
    image_name = "n8n_latest"
    container_name = "n8n_latest"

    subprocess.run(["docker", "rm", "-f", container_name], stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rmi", "-f", image_name], stderr=subprocess.DEVNULL)

    dockerfile_content = f"""
    FROM n8nio/n8n:latest
    ENTRYPOINT ["n8n"]
    """
    with open("Dockerfile.n8n", "w", encoding="utf-8") as f:
        f.write(dockerfile_content.strip())

    subprocess.run(
        ["docker", "build", "--pull", "-t", image_name, "-f", "Dockerfile.n8n", "."],
        check=True
    )
    subprocess.run([
        "docker", "run", "-d", "-p", f"{PORT}:5678", 
        "--name", container_name, "--env-file", ".env", 
        image_name], check=True)

    wait_for_n8n(N8N_URL, timeout=60)
    print("-" * 100)
    print(f"Open in Browser: {GREEN}{N8N_URL}{RESET}")

#---------------------------------------------------------------------------------

if __name__ == "__main__":
    docker_build_and_run_test()

#---------------------------------------------------------------------------------
# Docker Desktop vor dem Ausführen öffnen
# Ausführen kann 1-2 Minuten dauern
# Danach: Im Browser diese Adresse besuchen: http://localhost:5678
# Und irgendwelche Credentials eingeben (egal welche weil lokal)
#---------------------------------------------------------------------------------
# user:         someuser001@somerandomdomain.com    # z.B. 001 durch 002 ersetzen
# first:        User001                             # dito
# last:         User001                             # dito
# password:     some_password_001_tW3*$9Erg         # dito
#---------------------------------------------------------------------------------
# Hinweis:
# Wenn im Browser "cannot /GET o.ä." erscheint, dann paar Sek warten -> Refresh
#---------------------------------------------------------------------------------
# Dann "next" klicken (checkbox deaktiviert lassen)
# Dann "Get started" klicken (nichts auswählen)
# Dann "Skip" klicken
#---------------------------------------------------------------------------------
# Danach: 
# 1) Dort in der n8n UI unten links auf Zahnrad "Settings" klicken
# 2) Dort 'n8n API' klicken und API_KEY erstellen
# 3) Irgendeinen Namen für den API KEY wählen.
# 4) API KEY kopieren
# 5) In .env unter 'N8N_API_KEY=' einfügen
#---------------------------------------------------------------------------------


