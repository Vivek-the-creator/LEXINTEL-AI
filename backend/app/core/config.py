from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any, Optional


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "LexIntel AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "lexintel"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,gif,webp,mp3,wav,mp4,avi,mov,mkv"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── AI / LLM ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama3-8b-8192"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    LLM_STREAMING: bool = True

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # ── FAISS / Vector Store ──────────────────────────────────────────────────
    VECTOR_STORE_DIR: str = "./vector_store"
    VECTOR_STORE_INDEX_NAME: str = "lexintel_index"

    # ── RAG ───────────────────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 64
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7

    # ── Conversation Memory ───────────────────────────────────────────────────
    MEMORY_MAX_HISTORY: int = 20
    MEMORY_COLLECTION: str = "conversations"
    CASES_COLLECTION: str = "cases"

    # ── Phase 3A — Document Intelligence ─────────────────────────────────────
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "en"                # PaddleOCR language code
    OCR_USE_GPU: bool = False
    MAX_PDF_PAGES: int = 50
    MIN_TEXT_LENGTH_FOR_OCR: int = 100      # chars; below this → run OCR

    # ── Phase 3A — Legal Research ─────────────────────────────────────────────
    LEGAL_RAG_TOP_K: int = 8
    LEGAL_RAG_THRESHOLD: float = 0.35
    LEGAL_RESEARCH_INDEX: str = "legal_provisions"

    # ── Phase 3A — Similar Cases ──────────────────────────────────────────────
    CASES_RAG_TOP_K: int = 5
    CASES_RAG_THRESHOLD: float = 0.30
    CASES_INDEX: str = "case_judgments"

    @property
    def allowed_extensions_set(self) -> set:
        return {ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")}

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
