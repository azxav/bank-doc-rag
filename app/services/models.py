"""Pick an OpenRouter chat model, with a Luna fallback if the preferred id 404s."""

from __future__ import annotations

LUNA_FALLBACKS = (
    "openai/gpt-6-luna",
    "openai/gpt-6-luna-pro",
    "openai/gpt-5.6-luna",
    "openai/gpt-5.6-luna-pro",
    "~openai/gpt-luna-latest",
)


class ModelNotFoundError(RuntimeError):
    pass


def choose_chat_model(preferred: str, available: set[str] | list[str]) -> str:
    """Return `preferred` when OpenRouter lists it, otherwise the closest Luna chat id."""
    listed = set(available)
    if preferred in listed:
        return preferred
    usable = {
        model_id
        for model_id in listed
        if ":batch" not in model_id and "embed" not in model_id.lower()
    }
    for candidate in LUNA_FALLBACKS:
        if candidate in usable:
            return candidate
    luna = [model_id for model_id in usable if "luna" in model_id.lower()]
    if not luna:
        raise ModelNotFoundError(
            f"OpenRouter has no chat model for {preferred!r} and no Luna fallback."
        )
    luna.sort(key=lambda model_id: (0 if model_id.startswith("openai/") else 1, model_id))
    return luna[0]
