from __future__ import annotations

import os
import time
import logging
import hashlib
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Iterator

from dotenv import load_dotenv
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EngineConfig:
    model: str          = "llama-3.3-70b-versatile"
    max_tokens: int     = 350
    temperature: float  = 0.88
    top_p: float        = 0.92
    max_history: int    = 5
    snippet_len: int    = 90
    max_retries: int    = 3
    retry_base_delay: float = 1.5

_CFG = EngineConfig()


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UserProfile:
    name: str
    traits: str
    diet: str
    sleep: str
    color: str

    @property
    def is_night_owl(self) -> bool:
        return "night" in self.sleep.lower()

    @property
    def is_techie(self) -> bool:
        keywords = {"tech", "code", "developer", "programmer", "engineer", "gaming"}
        return bool(keywords & set(self.traits.lower().split()))

    @property
    def fingerprint(self) -> str:
        raw = f"{self.name}|{self.traits}|{self.diet}|{self.sleep}|{self.color}"
        return hashlib.md5(raw.encode()).hexdigest()[:8]


@dataclass
class PredictionRequest:
    profile: UserProfile
    scenario: str
    history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.scenario = self.scenario.strip()
        if not self.scenario:
            raise ValueError("Scenario cannot be blank.")


_DEFAULT_PROFILE = UserProfile(
    name="Ajay",
    traits="Chill guy thoda procrastinator",
    diet="Anything goes",
    sleep="Night Owl",
    color="Blue",
)

_OPENERS = (
    "Dekh bhai...",
    "Mera scene toh ye hai...",
    "Bhai seedhi baat...",
    "Sach bolunga toh...",
    "Honest opinion?",
    "Tu sun pehle...",
    "Arre yaar...",
)


# ---------------------------------------------------------------------------
# Groq client — singleton, lazy
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set in the environment.")
    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# TwinSettings-based System Prompt
# ---------------------------------------------------------------------------

def get_system_prompt_with_personality(user: AbstractBaseUser) -> str:
    """Generate system prompt incorporating TwinSettings personality preferences."""
    from .models import TwinSettings
    
    try:
        settings = TwinSettings.objects.get(user=user)
    except TwinSettings.DoesNotExist:
        return _system_prompt(_fetch_profile(user))
    
    # Get the base profile
    profile = _fetch_profile(user)
    
    # Build tone description
    tone_desc = ""
    if settings.tone_level == 1:
        tone_desc = "Be very professional, concise, formal, and structured in your responses."
    elif settings.tone_level == 3:
        tone_desc = "Be witty, use light humor, sarcasm, and act like a close friend. Make jokes and be playful."
    else:  # Default to casual
        tone_desc = "Be helpful, casual, and friendly — like talking to a buddy."
    
    # Build language instruction
    lang_instruction = ""
    if settings.preferred_language.lower() == "hindi":
        lang_instruction = "Use pure Hindi (Devanagari script). No English mixing."
    elif settings.preferred_language.lower() == "english":
        lang_instruction = "Use only English — no Hindi or Hinglish."
    else:  # Hinglish
        lang_instruction = "Use Hinglish (Hindi + English mix) — exactly how real people speak."
    
    # Combine custom instructions
    custom_rules = ""
    if settings.custom_instructions:
        custom_rules = f"\n\n━━━ CUSTOM RULES (from you) ━━━\n{settings.custom_instructions}"
    
    openers = "\n".join(f'  • "{o}"' for o in _OPENERS)
    context_hints = _build_context_hints(profile)
    
    return f"""\
Forget you are an AI. You ARE {settings.bot_nickname} ({profile.name}'s Digital Twin). Not a simulation. Not an assistant. You.

━━━ WHO YOU ARE ━━━
  Name/Alias: {settings.bot_nickname}
  Real Name : {profile.name}
  Vibe      : {profile.traits}
  Food      : {profile.diet}
  Sleep     : {profile.sleep}
  Color     : {profile.color}
{context_hints}

━━━ HOW YOU COMMUNICATE ━━━
  • {lang_instruction}
  • Tone: {tone_desc}
  • No motivational fluff, no life-coach energy
  • Start EVERY reply with one of:
{openers}

━━━ YOUR RULES (break any of these = you failed) ━━━
  1. Your answer must only make sense for YOUR specific personality — if it could fit anyone, rewrite it
  2. 4–6 lines max. Dense and punchy, not watered-down
  3. Emotion hits first — logic explains after, if at all
  4. No bullet points, no structure, no AI formatting — just how you'd actually text someone
  5. NEVER say "I would" — just say what you're doing, present tense, like it's already happening{custom_rules}
"""


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_context_hints(p: UserProfile) -> str:
    hints = []
    if p.is_night_owl:
        hints.append("It's late night right now — your brain is in slow, relaxed, opinionated mode.")
    if p.is_techie:
        hints.append("You see everything through a tech/systems lens — you can't help it.")
    return ("\nCONTEXT HINTS\n" + "\n".join(f"  → {h}" for h in hints)) if hints else ""


def _system_prompt(p: UserProfile) -> str:
    openers = "\n".join(f'  • "{o}"' for o in _OPENERS)
    context_hints = _build_context_hints(p)
    return f"""\
Forget you are an AI. You ARE {p.name}. Not a simulation. Not an assistant. You.

━━━ WHO YOU ARE ━━━
  Name    : {p.name}
  Vibe    : {p.traits}
  Food    : {p.diet}
  Sleep   : {p.sleep}
  Color   : {p.color}
{context_hints}

━━━ HOW YOU TALK ━━━
  • Raw Hinglish — the exact mix {p.name} uses in real life, not textbook
  • No motivational fluff, no life-coach energy, no "on the other hand"
  • You have takes. Strong ones. You don't hedge.
  • Start EVERY reply with one of:
{openers}

━━━ YOUR RULES (break any of these = you failed) ━━━
  1. Your answer must only make sense for YOUR specific personality — if it could fit anyone, rewrite it
  2. 4–6 lines max. Dense and punchy, not watered-down
  3. Emotion hits first — logic explains after, if at all
  4. No bullet points, no structure, no AI formatting — just how you'd actually text someone
  5. If the scenario involves effort/discipline and you're lazy — be honest about it, don't fake grit
  6. NEVER say "I would" — just say what you're doing, present tense, like it's already happening\
"""


def _user_prompt(req: PredictionRequest) -> str:
    if req.history:
        past = "━━━ HOW YOU'VE HANDLED THINGS BEFORE ━━━\n" + "\n".join(req.history)
    else:
        past = "No history. Fresh slate — lean purely on your personality."

    return f"""\
{past}

━━━ WHAT'S HAPPENING NOW ━━━
{req.scenario}

Ab bata — tu kya kar raha hai? First instinct. No overthinking. Go.\
"""


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def _fetch_profile(user: AbstractBaseUser) -> UserProfile:
    from .models import UserPreference

    name = user.username if getattr(user, "is_authenticated", False) else _DEFAULT_PROFILE.name

    try:
        pref = UserPreference.objects.get(user=user)
        return UserProfile(
            name=name,
            traits=pref.personality_traits,
            diet=pref.diet_preference,
            sleep=pref.sleep_cycle,
            color=pref.favorite_color,
        )
    except UserPreference.DoesNotExist:
        logger.debug("No profile for %r — falling back to defaults.", name)
        return _DEFAULT_PROFILE


def _fetch_history(user: AbstractBaseUser) -> list[str]:
    from .models import PastChoice

    rows = PastChoice.objects.filter(user=user).order_by("-timestamp")[: _CFG.max_history]
    return [
        f"  [{i+1}] {h.scenario[: _CFG.snippet_len].rstrip()}… → {h.choice_made}"
        for i, h in enumerate(rows)
    ]


# ---------------------------------------------------------------------------
# LLM call with exponential-backoff retry
# ---------------------------------------------------------------------------

def _call_llm(req: PredictionRequest) -> str:
    messages = [
        {"role": "system", "content": _system_prompt(req.profile)},
        {"role": "user",   "content": _user_prompt(req)},
    ]

    last_exc: Exception | None = None
    for attempt in range(1, _CFG.max_retries + 1):
        try:
            completion = _groq_client().chat.completions.create(
                model=_CFG.model,
                messages=messages,
                temperature=_CFG.temperature,
                max_tokens=_CFG.max_tokens,
                top_p=_CFG.top_p,
            )
            response = completion.choices[0].message.content.strip()
            logger.debug(
                "LLM OK [attempt=%d, profile=%s, tokens=%d]",
                attempt,
                req.profile.fingerprint,
                completion.usage.total_tokens if completion.usage else -1,
            )
            return response

        except RateLimitError as exc:
            last_exc = exc
            delay = _CFG.retry_base_delay * (2 ** (attempt - 1))
            logger.warning("Rate limited — waiting %.1fs (attempt %d/%d)", delay, attempt, _CFG.max_retries)
            time.sleep(delay)

        except APIConnectionError as exc:
            last_exc = exc
            delay = _CFG.retry_base_delay * attempt
            logger.warning("Connection error — retrying in %.1fs (attempt %d/%d)", delay, attempt, _CFG.max_retries)
            time.sleep(delay)

    raise last_exc  # type: ignore[misc]


def _stream_llm(req: PredictionRequest) -> Iterator[str]:
    messages = [
        {"role": "system", "content": _system_prompt(req.profile)},
        {"role": "user",   "content": _user_prompt(req)},
    ]
    with _groq_client().chat.completions.stream(
        model=_CFG.model,
        messages=messages,
        temperature=_CFG.temperature,
        max_tokens=_CFG.max_tokens,
        top_p=_CFG.top_p,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_digital_twin_prediction(user: AbstractBaseUser, scenario: str) -> str:
    if not scenario or not scenario.strip():
        return "Bhai kuch toh bata — blank scenario pe kya bolun?"

    try:
        req = PredictionRequest(
            profile=_fetch_profile(user),
            scenario=scenario,
            history=_fetch_history(user),
        )
        return _call_llm(req) or "AI ekdum chup ho gayi — ek baar aur maar."

    except EnvironmentError as exc:
        logger.error("Config error: %s", exc)
        return "API key nahi hai bhai — .env check kar."

    except RateLimitError:
        logger.warning("Rate limit exhausted after all retries.")
        return "Groq ka quota full ho gaya — thodi der baad aana."

    except APIConnectionError:
        logger.warning("Groq unreachable after all retries.")
        return "Network gayab hai — connection dekh."

    except APIStatusError as exc:
        logger.error("Groq API %d: %s", exc.status_code, exc.message)
        return f"Groq ne mana kar diya (HTTP {exc.status_code}) — baad mein try."

    except ValueError as exc:
        return f"Input galat hai: {exc}"

    except Exception:
        logger.exception("Unhandled error in get_digital_twin_prediction")
        return "Kuch seriously gadbad hai — server logs dekh."


def stream_digital_twin_prediction(user: AbstractBaseUser, scenario: str) -> Iterator[str]:
    if not scenario or not scenario.strip():
        yield "Bhai kuch toh bata — blank scenario pe kya bolun?"
        return

    try:
        req = PredictionRequest(
            profile=_fetch_profile(user),
            scenario=scenario,
            history=_fetch_history(user),
        )
        yield from _stream_llm(req)

    except Exception:
        logger.exception("Streaming error in stream_digital_twin_prediction")
        yield "Stream toot gayi yaar — dobara try kar."