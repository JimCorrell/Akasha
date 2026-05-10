from .config import settings

_MAX_CHARS = 32_000

# lazy-loaded backends
_fastembed_model = None
_openai_client = None


def _local_embed(text: str) -> list[float]:
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding

        print(f"Loading local embedding model: {settings.local_embedding_model}")
        _fastembed_model = TextEmbedding(settings.local_embedding_model)
    result = list(_fastembed_model.embed([text[:_MAX_CHARS]]))
    return result[0].tolist()


def _local_embed_batch(texts: list[str]) -> list[list[float]]:
    global _fastembed_model
    if _fastembed_model is None:
        from fastembed import TextEmbedding

        print(f"Loading local embedding model: {settings.local_embedding_model}")
        _fastembed_model = TextEmbedding(settings.local_embedding_model)
    return [v.tolist() for v in _fastembed_model.embed([t[:_MAX_CHARS] for t in texts])]


def _openai_embed(text: str) -> list[float]:
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    response = _openai_client.embeddings.create(
        input=text[:_MAX_CHARS],
        model=settings.openai_embedding_model,
    )
    return response.data[0].embedding


def _openai_embed_batch(texts: list[str]) -> list[list[float]]:
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    response = _openai_client.embeddings.create(
        input=[t[:_MAX_CHARS] for t in texts],
        model=settings.openai_embedding_model,
    )
    return [item.embedding for item in response.data]


def embed(text: str) -> list[float]:
    if settings.embedding_backend == "openai":
        return _openai_embed(text)
    return _local_embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    if settings.embedding_backend == "openai":
        return _openai_embed_batch(texts)
    return _local_embed_batch(texts)
