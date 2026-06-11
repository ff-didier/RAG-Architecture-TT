from __future__ import annotations

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings
from app.observability.fallbacks import ModelConfig, get_model_config

_anthropic_client: AsyncAnthropic | None = None
_openai_client: AsyncOpenAI | None = None


def get_anthropic_client() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def build_context(chunks: list) -> str:
    parts = []
    for chunk in chunks:
        parts.append(
            f"[Source: {chunk.filename} | chunk {chunk.chunk_index} | score {chunk.score:.4f}]\n{chunk.content}"
        )
    return "\n\n---\n\n".join(parts)


def _usage_from_anthropic(response) -> dict:
    usage = response.usage
    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
    return {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "provider": "anthropic",
    }


def _usage_from_openai(response) -> dict:
    usage = response.usage
    return {
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0,
        "provider": "openai",
    }


async def _generate_anthropic(model_config: ModelConfig, question: str, context: str) -> tuple[str, dict]:
    client = get_anthropic_client()
    system_prompt = model_config.compile_prompt(context=context, question=question)
    response = await client.messages.create(
        model=model_config.model,
        max_tokens=4096,
        temperature=model_config.temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    answer = "".join(text_blocks)
    usage = _usage_from_anthropic(response)
    usage["model"] = model_config.model
    usage["provider"] = model_config.provider
    return answer, usage


async def _generate_openai(model_config: ModelConfig, question: str, context: str) -> tuple[str, dict]:
    client = get_openai_client()
    prompt = model_config.compile_prompt(context=context, question=question)
    response = await client.chat.completions.create(
        model=model_config.model,
        temperature=model_config.temperature,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    answer = response.choices[0].message.content or ""
    usage = _usage_from_openai(response)
    usage["model"] = model_config.model
    usage["provider"] = model_config.provider
    return answer, usage


async def generate_answer(question: str, context: str) -> tuple[str, dict]:
    model_config = get_model_config()
    if model_config.provider == "openai":
        return await _generate_openai(model_config, question, context)
    return await _generate_anthropic(model_config, question, context)


async def _stream_anthropic(model_config: ModelConfig, question: str, context: str):
    client = get_anthropic_client()
    system_prompt = model_config.compile_prompt(context=context, question=question)
    async with client.messages.stream(
        model=model_config.model,
        max_tokens=4096,
        temperature=model_config.temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    ) as stream:
        async for text in stream.text_stream:
            if text:
                yield text


async def _stream_openai(model_config: ModelConfig, question: str, context: str):
    client = get_openai_client()
    prompt = model_config.compile_prompt(context=context, question=question)
    stream = await client.chat.completions.create(
        model=model_config.model,
        temperature=model_config.temperature,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield delta


async def stream_answer(question: str, context: str):
    model_config = get_model_config()
    if model_config.provider == "openai":
        async for token in _stream_openai(model_config, question, context):
            yield token
        return
    async for token in _stream_anthropic(model_config, question, context):
        yield token
