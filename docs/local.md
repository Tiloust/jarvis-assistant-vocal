# Mode local (100 % hors ligne) vs mode cloud

Jarvis tourne dans deux modes, choisis par une seule ligne dans `config.yaml` :

```yaml
mode: cloud    # cloud (Claude + ElevenLabs) | local (Ollama + Piper, 100% offline)
```

| | **cloud** (defaut) | **local** |
|---|---|---|
| LLM | Claude (API Anthropic) | Ollama (`qwen2.5:7b`...) |
| Voix (TTS) | ElevenLabs | Piper (FR) |
| Transcription (STT) | faster-whisper (local) | faster-whisper (local) |
| Qualite | maximale | bonne (dépend du modèle) |
| Cout | à l'usage (API) | gratuit |
| Vie privée | appels API | **rien ne sort de la machine** |
| Matériel | léger | GPU recommandé (voir plus bas) |

Le **STT est déjà local dans les deux modes** (faster-whisper, GPU si dispo).

## Passer en mode local

1. **Ollama** : installe [ollama.com](https://ollama.com), puis récupère un modèle
   qui gère bien le *function calling* :
   ```bash
   ollama pull qwen2.5:7b        # recommandé (ou llama3.1:8b)
   ```
2. **Voix Piper** (français) : télécharge une voix depuis
   [Piper FR](https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR)
   (ex. `fr_FR-siwis-medium`), place le `.onnx` **et** son `.json` dans `voix/`.
3. Dans `config.yaml` : `mode: local` (et éventuellement `ollama.modele`,
   `piper.modele`).

Sans clé Claude ni ElevenLabs, le mode local fonctionne entièrement seul. (Si Piper
n'est pas configuré, Jarvis retombe sur la voix Windows SAPI.)

## Fiabilité réelle du mode local (honnête)

Testé avec `qwen2.5:7b` sur cette base de code :

- ✅ **Les outils du quotidien marchent bien et vite** (1,6–5 s par tour) : lumières
  Hue, ambiances/scènes, OBS, minuteurs, heure, météo, mémoire, volume/média...
- ⚠️ **Un petit modèle 7b se noie avec trop d'outils.** Jarvis n'expose donc au
  modèle local qu'un **jeu réduit (24 outils sur 50)**, ciblé et fiable. Avec les 50
  outils, `qwen2.5:7b` devenait lent (>60 s) et ratait ses appels.
- ❌ **Vision impossible en local.** Les modèles locaux ci-dessus n'ont pas de
  vision : tout ce qui repose sur des captures d'écran (assistance navigateur,
  réservation web pilotée, `capture_screen`) reste **cloud**.

### Récupération sur échec d'appel d'outil

Si le modèle local rate un appel d'outil (JSON invalide), `OllamaProvider` **réessaie
une fois** avec une consigne plus directive, puis renvoie un message d'erreur clair
plutôt que de planter.

## Matrice de compatibilité des outils

| Catégorie | Outils | cloud | local |
|---|---|---|---|
| Domotique / PC | Hue, scènes, OBS, stats, volume, apps | ✅ | ✅ |
| Utilitaires | minuteur, heure, mémoire, personnalité, présence | ✅ | ✅ |
| Météo / web | météo, recherche web | ✅ | ✅ si en ligne\* |
| Productivité internet | Gmail, Google Agenda, deadlines, brief | ✅ | ☁️ cloud recommandé |
| Communication | Discord, Instagram, appels Twilio | ✅ | ☁️ cloud recommandé |
| Vision / agentique | réservation web, assistance navigateur, capture écran | ✅ | ❌ (vision requise) |
| Serveur MCP | domotique/PC exposés | ✅ | ✅ |

\* Les outils internet ne sont pas proposés au modèle local et, plus généralement,
échouent proprement avec un message clair s'il n'y a pas de réseau.

**En résumé** : le mode local couvre très bien la **domotique et le PC** en tout
confidentialité ; pour la **productivité internet** et surtout les **features à
vision** (navigateur, réservation), le **mode cloud est recommandé**. Ces dernières
utilisent Claude pour la boucle vision, même quand `mode: local` — il suffit d'une
clé `anthropic.cle`.

## Matériel recommandé (mode local)

- **faster-whisper** `medium` : ~2–3 Go de VRAM (GPU) ; repli CPU possible mais lent.
- **qwen2.5:7b** (quantifié Q4) : ~5 Go de VRAM.
- Une carte **8 Go de VRAM** (ex. RTX 2070/3060) fait tourner les deux, c'est juste
  mais jouable. Sinon, `qwen2.5:3b` est plus léger (moins fiable sur les outils).
- Piper : négligeable, temps réel sur CPU.

## Kokoro vs Piper (pourquoi Piper)

Kokoro (`kokoro-onnx`) ne propose qu'**une** voix française récente, de qualité
moyenne. **Piper** a plusieurs voix FR éprouvées (`fr_FR-siwis`, `fr_FR-tom`...), est
ultra-léger et temps réel sur CPU, et est déjà intégré au projet. C'est le meilleur
choix pour un TTS local français aujourd'hui — d'où le `PiperProvider` fourni.
