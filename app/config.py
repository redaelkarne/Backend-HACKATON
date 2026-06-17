from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/strava/callback"
    strava_frontend_url: str = "http://localhost:5173/activites/nouvelle"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
