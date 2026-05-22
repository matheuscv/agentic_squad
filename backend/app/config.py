from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Carrega variáveis de ambiente do arquivo .env como atributos tipados."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./contatos.db"
    # Ambiente de execução: "development" (logs texto) ou "production" (logs JSON).
    # Lido da variável de ambiente ENV; default conservador para DEV.
    env: str = "development"
    # Origens permitidas no CORS (separadas por vírgula).
    # Em produção, definir como a URL do Vercel: https://seu-app.vercel.app
    cors_origins: str = "http://localhost:3000,http://localhost:3002"


# Instância global — importar de outros módulos com: from app.config import settings
settings = Settings()
