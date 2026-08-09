"""Abstraction du modele de langage : le reste du code ignore quel provider tourne.

Trois implementations, choisies par config.yaml (mode: cloud | local | gemini) :
  - ClaudeProvider  : API Anthropic (cloud, defaut).
  - OllamaProvider  : Ollama en local (http://localhost:11434), 100% offline.
  - GeminiProvider  : API Google Gemini (cloud, alternative a Claude).

Les trois exposent la meme methode `repondre(systeme, historique, outils)` et
renvoient un objet a la forme d'une reponse Anthropic (.stop_reason + .content,
chaque bloc ayant .type / .text / .name / .input / .id). Ainsi la boucle de
dialogue de jarvis14 ne change pas selon le provider.

L'historique reste au format "content blocks" d'Anthropic ; OllamaProvider et
GeminiProvider le traduisent vers/depuis leur propre format de facon interne.
"""
import json
import logging

# Magasin de certificats Windows (Malwarebytes intercepte le TLS : sans ca, les
# appels a l'API Anthropic echouent en "certificate verify failed").
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from core.config import reglage

LOG = logging.getLogger("jarvis")


class Bloc:
    """Imite un bloc de contenu Anthropic (text ou tool_use)."""

    def __init__(self, type, text=None, id=None, name=None, input=None):
        self.type = type
        self.text = text
        self.id = id
        self.name = name
        self.input = input


class Reponse:
    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason
        self.content = content


# --------------------------------------------------------------- interface

class ProviderLLM:
    nom = "?"

    def disponible(self):
        return True

    def repondre(self, systeme, historique, outils):
        raise NotImplementedError


# --------------------------------------------------------------- Claude (cloud)

class ClaudeProvider(ProviderLLM):
    nom = "Claude"

    def __init__(self):
        import anthropic
        cle = reglage("anthropic.cle", "")
        self.modele = reglage("anthropic.modele", "claude-haiku-4-5")
        self.client = anthropic.Anthropic(api_key=cle) if cle else None

    def disponible(self):
        return self.client is not None

    def repondre(self, systeme, historique, outils):
        # La reponse native Anthropic a deja la bonne forme (.stop_reason/.content).
        return self.client.messages.create(
            model=self.modele,
            max_tokens=1024,
            system=[{"type": "text", "text": systeme,
                     "cache_control": {"type": "ephemeral"}}],
            messages=historique,
            tools=outils,
        )


# --------------------------------------------------------------- Gemini (cloud)

class GeminiProvider(ProviderLLM):
    """Provider Google Gemini (SDK google-genai). Alternative a Claude, meme role.

    Necessite : uv add google-genai
    Config : gemini.cle (cle API, https://aistudio.google.com/apikey) et
             gemini.modele (defaut "gemini-2.5-flash").

    Limite connue : la vision (captures d'ecran) n'est pas traduite ici, comme
    pour OllamaProvider. Les outils texte/fonction sont, eux, pleinement geres.
    """
    nom = "Gemini"

    def __init__(self):
        from google import genai
        cle = reglage("gemini.cle", "")
        self.modele = reglage("gemini.modele", "gemini-2.5-flash")
        self.client = genai.Client(api_key=cle) if cle else None

    def disponible(self):
        return self.client is not None

    # -- traduction historique Anthropic -> contents Gemini --
    def _traduire(self, historique):
        from google.genai import types
        contents = []
        for m in historique:
            role, contenu = m.get("role"), m.get("content")
            role_gemini = "model" if role == "assistant" else "user"
            parts = []
            if isinstance(contenu, str):
                parts.append(types.Part.from_text(text=contenu))
            else:
                for item in contenu or []:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_result":
                            c = item.get("content")
                            if isinstance(c, list):  # bloc image
                                c = "[image capturee - la vision n'est pas traduite pour Gemini]"
                            parts.append(types.Part.from_function_response(
                                name=item.get("tool_use_id", "outil"),
                                response={"resultat": str(c)}))
                        elif item.get("type") == "image":
                            parts.append(types.Part.from_text(
                                text="[image - vision non traduite pour Gemini]"))
                    else:  # bloc Anthropic (objet Bloc ou reponse native)
                        t = getattr(item, "type", None)
                        if t == "text" and getattr(item, "text", None):
                            parts.append(types.Part.from_text(text=item.text))
                        elif t == "tool_use":
                            parts.append(types.Part.from_function_call(
                                name=item.name, args=item.input or {}))
            if parts:
                contents.append(types.Content(role=role_gemini, parts=parts))
        return contents

    def _outils(self, outils):
        from google.genai import types
        if not outils:
            return None
        declarations = [
            types.FunctionDeclaration(
                name=o["name"],
                description=o.get("description", ""),
                parameters=o.get("input_schema", {"type": "object", "properties": {}}),
            )
            for o in outils
        ]
        return [types.Tool(function_declarations=declarations)]

    def repondre(self, systeme, historique, outils):
        from google.genai import types
        contents = self._traduire(historique)
        tools = self._outils(outils)
        config = types.GenerateContentConfig(
            system_instruction=systeme,
            tools=tools,
            max_output_tokens=1024,
        )
        try:
            rep = self.client.models.generate_content(
                model=self.modele, contents=contents, config=config)
        except Exception:
            LOG.exception("gemini: echec de l'appel API")
            return Reponse("end", [Bloc("text", text=(
                "Desole, l'appel a Gemini a echoue. Verifie ta cle API et ta "
                "connexion, ou repasse en mode cloud (Claude) / local (Ollama)."))])

        blocs = []
        try:
            candidat = rep.candidates[0]
            for part in candidat.content.parts:
                if getattr(part, "text", None):
                    blocs.append(Bloc("text", text=part.text))
                fc = getattr(part, "function_call", None)
                if fc:
                    blocs.append(Bloc("tool_use", id=f"call_{fc.name}",
                                       name=fc.name,
                                       input=dict(fc.args) if fc.args else {}))
        except Exception:
            LOG.exception("gemini: erreur de parsing de la reponse")
            if not blocs:
                blocs = [Bloc("text", text="Desole, reponse Gemini illisible.")]

        stop = "tool_use" if any(b.type == "tool_use" for b in blocs) else "end"
        return Reponse(stop, blocs)


# --------------------------------------------------------------- Ollama (local)

class OllamaProvider(ProviderLLM):
    nom = "Ollama"

    def __init__(self):
        self.hote = reglage("ollama.hote", "http://localhost:11434").rstrip("/")
        self.modele = reglage("ollama.modele", "qwen3.5:4b")

    def disponible(self):
        try:
            import requests
            requests.get(f"{self.hote}/api/version", timeout=3)
            return True
        except Exception:
            return False

    # -- traduction historique Anthropic -> messages Ollama --
    def _traduire(self, systeme, historique):
        messages = [{"role": "system", "content": systeme}]
        for m in historique:
            role, contenu = m.get("role"), m.get("content")
            if role == "user":
                if isinstance(contenu, str):
                    messages.append({"role": "user", "content": contenu})
                else:
                    for item in contenu or []:
                        if not isinstance(item, dict):
                            continue
                        if item.get("type") == "tool_result":
                            c = item.get("content")
                            if isinstance(c, list):   # bloc image
                                c = "[image capturee - la vision n'est pas disponible en mode local]"
                            messages.append({"role": "tool", "content": str(c)})
                        elif item.get("type") == "image":
                            messages.append({"role": "user",
                                             "content": "[image - vision indisponible en local]"})
            else:  # assistant
                if isinstance(contenu, str):
                    messages.append({"role": "assistant", "content": contenu})
                else:
                    texte = " ".join(b.text for b in (contenu or [])
                                     if getattr(b, "type", None) == "text" and b.text)
                    appels = [b for b in (contenu or []) if getattr(b, "type", None) == "tool_use"]
                    msg = {"role": "assistant", "content": texte}
                    if appels:
                        msg["tool_calls"] = [
                            {"function": {"name": b.name, "arguments": b.input or {}}}
                            for b in appels]
                    messages.append(msg)
        return messages

    def _outils(self, outils):
        return [{"type": "function", "function": {
            "name": o["name"], "description": o["description"],
            "parameters": o.get("input_schema", {"type": "object", "properties": {}})}}
            for o in outils]

    def _chat(self, messages, tools, nudge=None):
        import requests
        if nudge:
            messages = messages + [{"role": "user", "content": nudge}]
        # think=false : desactive le "raisonnement" natif (qwen3.5, etc.). Sinon le
        # modele est tres lent et rend parfois ses appels d'outils en texte au lieu
        # de les executer. Un modele sans thinking ignore ce parametre.
        r = requests.post(f"{self.hote}/api/chat", timeout=120, json={
            "model": self.modele, "messages": messages, "tools": tools,
            "stream": False, "think": bool(reglage("ollama.think", False)),
            "options": {"temperature": 0.3}})
        r.raise_for_status()
        return r.json()

    def _parser(self, rep):
        msg = rep.get("message", {}) or {}
        blocs = []
        texte = (msg.get("content") or "").strip()
        if texte:
            blocs.append(Bloc("text", text=texte))
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function", {}) or {}
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)   # peut lever -> gere par le retry
            blocs.append(Bloc("tool_use", id=f"call_{i}", name=fn.get("name"), input=args or {}))
        stop = "tool_use" if any(b.type == "tool_use" for b in blocs) else "end"
        return Reponse(stop, blocs)

    def repondre(self, systeme, historique, outils):
        messages = self._traduire(systeme, historique)
        tools = self._outils(outils)
        try:
            return self._parser(self._chat(messages, tools))
        except Exception as e:
            LOG.warning("ollama: 1er essai en echec (%s), retry plus directif", e)
            # Retry unique, avec une consigne plus stricte sur l'appel d'outil.
            nudge = ("Rappel : pour agir, appelle l'outil approprie via un tool call "
                     "avec des arguments JSON valides ; sinon reponds simplement en texte.")
            try:
                return self._parser(self._chat(messages, tools, nudge=nudge))
            except Exception:
                LOG.exception("ollama: echec apres retry")
                return Reponse("end", [Bloc("text", text=(
                    "Desole, le modele local n'a pas reussi a traiter la demande "
                    "correctement. Reessaie en reformulant, ou repasse en mode cloud."))])


# --------------------------------------------------------------- fabrique

_LLM = None


def llm():
    """Provider LLM courant (selon config.yaml mode: cloud|local|gemini)."""
    global _LLM
    if _LLM is None:
        mode = (reglage("mode", "cloud") or "cloud").lower()
        if mode == "local":
            _LLM = OllamaProvider()
        elif mode == "gemini":
            _LLM = GeminiProvider()
        else:
            _LLM = ClaudeProvider()
        LOG.info("provider LLM : %s (mode %s)", _LLM.nom, mode)
    return _LLM
