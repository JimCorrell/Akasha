from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    threshold: float = 0.0  # minimum cosine similarity (0–1)


class NoteResult(BaseModel):
    title: str
    path: str
    snippet: str
    score: float
    tags: list[str]
    modified: str | None


class SearchResponse(BaseModel):
    results: list[NoteResult]
    query_time_ms: float
    total_notes: int


class StatsResponse(BaseModel):
    total_notes: int
    vault_path: str
    chroma_path: str
    embedding_model: str


class AskRequest(BaseModel):
    question: str
    limit: int = 6  # notes to retrieve as context


class AskResponse(BaseModel):
    answer: str
    sources: list[NoteResult]
    query_time_ms: float


class IngestRequest(BaseModel):
    path: str  # absolute path to the .epub or .pdf file


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    messages: list[str]
    result: str | None = None  # vault-relative path to the book index note
    error: str | None = None
