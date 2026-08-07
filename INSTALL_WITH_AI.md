# Installer Jarvis avec l'aide d'une IA

Ce guide est pensé pour être **collé dans un assistant IA** (Claude, ChatGPT, Copilot…)
ou suivi pas à pas à la main. Il installe Jarvis en mode cloud (le plus simple), puis
liste les intégrations optionnelles.

> Prérequis : **Windows 11**, un **microphone**, et une connexion internet. Un **GPU
> NVIDIA** est recommandé (transcription plus rapide) mais pas obligatoire.

---

## À coller dans ton IA

> Tu es mon assistant d'installation. Aide-moi à installer le projet
> **jarvis-assistant-vocal** sur Windows 11, une étape à la fois, en attendant ma
> confirmation entre chaque étape. Voici les étapes :
>
> 1. Vérifie que **Python 3.13** est installé (`python --version`). Sinon, guide-moi.
> 2. Installe **uv** (le gestionnaire de paquets) :
>    `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
> 3. Dans le dossier du projet : `uv sync` (installe les dépendances).
> 4. `uv run playwright install chromium` (pour les réservations web et le navigateur).
> 5. Copie la config : `copy config.example.yaml config.yaml`.
> 6. Ouvre `config.yaml` et aide-moi à mettre au minimum **`anthropic.cle`** (ma clé
>    depuis console.anthropic.com). Explique-moi chaque autre section quand je le demande.
> 7. Lance : `uv run python jarvis14.py`, puis je dis « Hey Jarvis ».
>
> Ne passe à l'étape suivante que quand je confirme que la précédente a marché. Si une
> commande échoue, diagnostique l'erreur avant de continuer.

---

## Version manuelle (résumé)

```bash
# 1. uv (si absent)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. dépendances
uv sync
uv run playwright install chromium

# 3. config
copy config.example.yaml config.yaml
#    -> édite config.yaml, mets au minimum anthropic.cle

# 4. lancer
uv run python jarvis14.py
```

Dis **« Hey Jarvis »**. Sous Windows, tu peux aussi double-cliquer `lancer_jarvis.bat`.

## Le strict minimum

- **Mode cloud** : une clé `anthropic.cle` ([console.anthropic.com](https://console.anthropic.com/)) suffit à tout faire fonctionner. La voix par défaut est celle de Windows ; pour une meilleure voix, ajoute une clé ElevenLabs (optionnel).
- **Mode local** (100 % hors ligne) : installe [Ollama](https://ollama.com), `ollama pull qwen2.5:7b`, mets `mode: local`. Voir [docs/local.md](docs/local.md).

## Intégrations optionnelles

Chacune a son guide dans `docs/` — active seulement ce qui t'intéresse :

- 💡 [Philips Hue](docs/hue.md) · 🎬 [OBS](docs/obs.md) · 📅 [Google Agenda](docs/agenda.md)
- 🏠 [Présence](docs/presence.md) · 💬 [Discord](docs/discord.md) · 📞 [Twilio](docs/appels.md)
- 🌐 [Navigateur](docs/navigateur.md) · 🍽️ [Réservations](docs/reservation.md)
- 📸 [Instagram](docs/instagram.md) · 🔌 [Serveur MCP](docs/mcp.md)

## Dépannage rapide

- **« aucune clé Claude »** au démarrage → `anthropic.cle` manquante dans `config.yaml`.
- **Whisper lent** → pas de GPU détecté ; ça marche en CPU mais c'est plus lent.
- **Le micro n'entend rien** → vérifie l'index `audio.micro` (voir
  `sounddevice.query_devices()`).
