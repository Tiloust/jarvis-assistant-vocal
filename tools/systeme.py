"""Outils systeme Windows : lancer une application, controler le media, le volume."""
import ctypes
import os
import subprocess
import time
import webbrowser
from pathlib import Path

from core.registre import outil

# Codes des touches multimedia Windows
_TOUCHES = {
    "muet": 0xAD,
    "baisser": 0xAE,
    "monter": 0xAF,
    "suivant": 0xB0,
    "precedent": 0xB1,
    "pause": 0xB3,
}


def _presser(code, fois=1):
    for _ in range(fois):
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)
        time.sleep(0.02)


@outil(
    nom="ouvrir_application",
    description="Lance une application ou ouvre un site web",
    parametres={
        "type": "object",
        "properties": {
            "nom": {
                "type": "string",
                "description": "Nom de l'application ou du site "
                               "(spotify, discord, youtube, calculatrice...)",
            }
        },
        "required": ["nom"],
    },
)
def ouvrir_application(nom: str) -> str:
    """Lance une application ou un site."""
    nom_min = nom.lower().strip()

    raccourcis = {
        "spotify": "spotify:",
        "discord": None,  # traite plus bas
        "navigateur": "https://www.google.com",
        "internet": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "calculatrice": "calc",
        "bloc-notes": "notepad",
        "explorateur": "explorer",
        "parametres": "ms-settings:",
    }

    if nom_min == "discord":
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Discord"
        maj = base / "Update.exe"
        if maj.exists():
            subprocess.Popen([str(maj), "--processStart", "Discord.exe"])
            return "Discord lance."
        return "Discord introuvable."

    cible = raccourcis.get(nom_min, nom)

    try:
        if str(cible).startswith("http"):
            webbrowser.open(cible)
        else:
            subprocess.Popen(f'start "" "{cible}"', shell=True)
        return f"{nom} lance."
    except Exception as e:
        return f"Impossible de lancer {nom} : {e}"


@outil(
    nom="controler_media",
    description="Controle la lecture audio ou video en cours",
    parametres={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["pause", "suivant", "precedent", "muet"],
                "description": "Action a effectuer",
            }
        },
        "required": ["action"],
    },
)
def controler_media(action: str) -> str:
    """Controle la lecture et le volume.

    action : pause, suivant, precedent, monter, baisser, muet
    """
    action = action.lower().strip()
    if action not in _TOUCHES:
        return f"Action inconnue : {action}"

    fois = 5 if action in ("monter", "baisser") else 1
    _presser(_TOUCHES[action], fois)
    return f"Fait : {action}."


@outil(
    nom="regler_volume",
    description="Monte ou baisse le volume du systeme",
    parametres={
        "type": "object",
        "properties": {
            "sens": {"type": "string", "enum": ["monter", "baisser"]},
            "crans": {
                "type": "integer",
                "description": "Nombre de crans, 2 % chacun. 10 par defaut.",
            },
        },
        "required": ["sens"],
    },
)
def regler_volume(sens: str, crans: int = 10) -> str:
    """Monte ou baisse le volume d'un nombre de crans (2 % par cran)."""
    sens = sens.lower().strip()
    if sens not in ("monter", "baisser"):
        return "Sens invalide."
    _presser(_TOUCHES[sens], max(1, min(crans, 50)))
    return f"Volume {sens}."
