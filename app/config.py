from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Relatórios Processuais IA"
    APP_USERNAME: str = "admin"
    APP_PASSWORD: str = "troque-esta-senha"
    SESSION_SECRET: str = "troque-esta-chave-secreta"
    OPENAI_API_KEY: str = ""
    DATAJUD_API_KEY: str = ""
    DATAJUD_ENABLED: bool = False
    DATA_PROVIDER: str = "mock"  # mock | datajud

    class Config:
        env_file = ".env"

settings = Settings()
