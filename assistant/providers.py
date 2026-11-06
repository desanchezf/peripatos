"""Proveedores de modelos. Todos emiten los mismos eventos, y el frontal no depende de cuál responde:

    {"type": "text", "text": ...}
    {"type": "usage", "input_tokens": ..., "output_tokens": ...}
"""

import anthropic
import httpx
import ollama
from django.conf import settings

from .models import LLMModel

SYSTEM_PROMPT = (
    "Eres el asistente de Peripatos, una plataforma de formación con lecturas, cuestionarios, "
    "laboratorios y roadmaps. Ayudas a estudiar y a resolver dudas. Todavía no puedes consultar los "
    "datos de la plataforma: si te preguntan por ellos, dilo en lugar de suponerlos. "
    "Responde en el idioma del usuario."
)

# Las conversaciones de estudio no necesitan más. Opus 5.5 y Haiku 5.5 ya usan medium por defecto; Sonnet 5.5, high
EFFORT = "medium"
EFFORT_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-1"}
# Si el clasificador de seguridad rechaza la petición, la API la repite en el modelo que recomienda Anthropic
REFUSAL_FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"}

# Ollama usa 4096 tokens si no se le indica otra cosa, y lo que no cabe lo recorta sin avisar
OLLAMA_CONTEXT = 8192


class ProviderError(Exception):
    """Error del proveedor que se muestra al usuario."""


def describe_anthropic_error(exc):
    if isinstance(exc, anthropic.AuthenticationError):
        return "La API key de Anthropic no es válida."
    if isinstance(exc, anthropic.NotFoundError):
        return "El modelo no existe o la cuenta no tiene acceso."
    if isinstance(exc, anthropic.RateLimitError):
        return "Límite de peticiones de Anthropic alcanzado. Inténtalo en unos segundos."
    if isinstance(exc, anthropic.APIStatusError):
        return f"Error de la API de Anthropic ({exc.status_code}): {exc.message}"
    if isinstance(exc, anthropic.APIConnectionError):
        return "No se pudo conectar con la API de Anthropic."
    return str(exc)


def stream_anthropic(name, history):
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    # max_tokens alto: en streaming no hay riesgo de timeout HTTP
    params = {
        "model": name,
        "max_tokens": 64000,
        "system": SYSTEM_PROMPT,
        "messages": history,
        # El historial se reenvía en cada turno: cacheado cuesta ~0,1x
        "cache_control": {"type": "ephemeral"},
    }
    if name in EFFORT_MODELS:
        params["output_config"] = {"effort": EFFORT}
    stream = client.messages.stream
    if name in REFUSAL_FALLBACK_MODELS:
        stream = client.beta.messages.stream
        params.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")

    try:
        with stream(**params) as response_stream:
            for event in response_stream:
                if event.type == "text":
                    yield {"type": "text", "text": event.text}
            response = response_stream.get_final_message()
    except anthropic.APIError as exc:
        raise ProviderError(describe_anthropic_error(exc)) from exc

    yield {"type": "usage", "input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    if response.stop_reason == "refusal":
        raise ProviderError("El modelo ha rechazado la petición.")
    if response.stop_reason == "max_tokens":
        raise ProviderError("La respuesta se cortó por superar la longitud máxima.")


def stream_ollama(name, history):
    client = ollama.Client(host=settings.OLLAMA_BASE_URL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    try:
        for chunk in client.chat(model=name, messages=messages, stream=True, options={"num_ctx": OLLAMA_CONTEXT}):
            if chunk.message.content:
                yield {"type": "text", "text": chunk.message.content}
            if chunk.done:
                yield {"type": "usage", "input_tokens": chunk.prompt_eval_count or 0, "output_tokens": chunk.eval_count or 0}
    except ollama.ResponseError as exc:
        if exc.status_code == 404:
            raise ProviderError(f"El modelo {name} no está descargado en Ollama.") from exc
        raise ProviderError(f"Ollama: {exc.error}") from exc
    # En streaming, la librería deja pasar los errores de httpx sin convertirlos en ConnectionError
    except (ConnectionError, httpx.TransportError) as exc:
        raise ProviderError("No se pudo conectar con Ollama. ¿Está levantado el perfil ollama de Docker Compose?") from exc


def stream_chat(model, history):
    streams = {LLMModel.Provider.ANTHROPIC: stream_anthropic, LLMModel.Provider.OLLAMA: stream_ollama}
    return streams[model.provider](model.name, history)
