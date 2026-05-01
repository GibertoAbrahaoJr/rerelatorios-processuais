from pydantic_settings import BaseSettings

# API Key pública atual do DataJud/CNJ, publicada na Wiki oficial do CNJ.
# Pode ser alterada pelo CNJ a qualquer momento. No Render, você pode sobrescrever
# criando a variável de ambiente DATAJUD_API_KEY.
DEFAULT_DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

class Settings(BaseSettings):
    APP_NAME: str = "Relatórios Processuais IA"
    APP_USERNAME: str = "admin"
    APP_PASSWORD: str = "troque-esta-senha"
    SESSION_SECRET: str = "troque-esta-chave-secreta"
    OPENAI_API_KEY: str = ""

    # Agora o padrão já tenta consultar o DataJud/CNJ.
    DATA_PROVIDER: str = "datajud"  # datajud | mock
    DATAJUD_ENABLED: bool = True
    DATAJUD_API_KEY: str = DEFAULT_DATAJUD_API_KEY
    DATAJUD_TIMEOUT_SECONDS: int = 30
    DATAJUD_MAX_MOVIMENTOS: int = 12

    class Config:
        env_file = ".env"

settings = Settings()
