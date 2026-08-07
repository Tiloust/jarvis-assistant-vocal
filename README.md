# Jarvis — assistant vocal local (français)

Assistant vocal en français qui tourne **sur ta machine**. Mot d'activation
« Hey Jarvis », transcription locale (Whisper), raisonnement par **Claude** avec
une boîte à outils extensible, synthèse vocale ElevenLabs (repli voix Windows).
Une interface « réacteur arc » optionnelle s'ouvre dans le navigateur.

**Chaîne audio :** openWakeWord → faster-whisper → Claude (+ outils) → ElevenLabs / SAPI.

> ⚠️ Projet personnel partagé tel quel. Il cible **Windows 11** et suppose un
> micro + des clés d'API (au minimum Anthropic). Beaucoup d'intégrations sont
> **optionnelles** : sans leur clé, l'outil correspondant se désactive proprement.

## Ce que Jarvis sait faire

Chaque capacité est un **outil** dans `tools/` (architecture modulaire : ajouter un
fichier suffit à ajouter un outil). Actuellement :

- **Domotique** — Philips Hue (allumer, luminosité, couleur), ambiances/scènes,
  détection de présence (ping du téléphone) pour des modes automatiques.
- **PC & streaming** — OBS (stream, enregistrement, scènes, replay), stats système
  (GPU/CPU/RAM), lancement d'applications, contrôle média/volume, capture d'écran.
- **Productivité** — Google Agenda (lecture de tous les agendas, création/suppression
  avec confirmation), Gmail, brief du matin, mémoire long terme, minuteurs, météo.
- **Web** — recherche, **réservation** pilotée par Claude (Playwright : TheFork,
  Doctolib, formulaires génériques), **assistance sur ton vrai Chrome** (résumer une
  page, gérer les onglets, agir — avec domaines protégés en lecture seule).
- **Communication** — résumé Discord (mentions + messages du jour), analyse
  **Instagram** (abonnés & vues vs la veille, multi-comptes), **appels téléphoniques**
  Twilio (message simple, ou conversation temps réel).
- **Serveur MCP** — expose les outils domotique/PC à n'importe quel client MCP
  (Claude Desktop, etc.), avec liste blanche par outil. Voir [docs/mcp.md](docs/mcp.md).

**Sécurité intégrée** : les actions irréversibles (envoi de mail, réservation,
appel, suppression…) demandent une **confirmation vocale** ; jamais de saisie de
mot de passe ni de paiement automatique ; domaines sensibles (banque, impôts, santé)
en lecture seule sur le vrai navigateur ; secrets jamais versionnés.

## Installation

Prérequis : **Python 3.13**, [uv](https://docs.astral.sh/uv/), Windows 11, un micro.
GPU NVIDIA recommandé (Whisper), sinon repli CPU.

```bash
uv sync
uv run playwright install chromium   # pour la réservation web
```

### Configuration

Toute la config (clés d'API et réglages) est dans un seul fichier **non versionné**.
Copie le modèle et remplis ce dont tu as besoin :

```bash
copy config.example.yaml config.yaml
```

`config.example.yaml` documente **chaque clé** et où l'obtenir. Le strict minimum est
`anthropic.cle` (une clé [console.anthropic.com](https://console.anthropic.com/)).
Tout le reste est optionnel. Guides détaillés par intégration :

- [docs/mcp.md](docs/mcp.md) — serveur MCP (Claude Desktop, Hermes)
- [docs/reservation.md](docs/reservation.md) — réservation web
- [docs/navigateur.md](docs/navigateur.md) — assistance sur ton Chrome
- [docs/agenda.md](docs/agenda.md) — Google Agenda + deadlines iCal
- [docs/appels.md](docs/appels.md) — appels téléphoniques Twilio
- [docs/instagram.md](docs/instagram.md) — analyse Instagram

### Voix (optionnel)

Sans clé ElevenLabs, Jarvis utilise la voix Windows. Pour une voix Piper locale,
place un modèle `.onnx` (+ `.json`) dans `voix/` (voir
[voix Piper FR](https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR)).

## Lancement

```bash
uv run python jarvis14.py
```

Puis dis « **Hey Jarvis** ». Sous Windows, tu peux double-cliquer `lancer_jarvis.bat`.

## Confidentialité

`config.yaml` (secrets), `memory.json` (mémoire), `logs/` (dont les transcriptions
d'appels), les profils navigateur et les tokens OAuth **ne sont jamais versionnés**
(voir `.gitignore`). Rien de personnel ne quitte ta machine, hormis les appels aux
API que tu configures (Claude, ElevenLabs, etc.).

## Licence

MIT — voir [LICENSE](LICENSE).
