from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    IMWEB_API_KEY: str
    IMWEB_SECRET_KEY: str
    IMWEB_AGENCY_CATEGORY: str | None = None
    IMWEB_BASE_URL: str = "https://api.imweb.me/v2"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
