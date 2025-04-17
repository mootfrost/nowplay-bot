from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from app.MusicProvider.auth import get_encoded_creds


class OauthCreds(BaseModel):
    client_id: str
    client_secret: str
    redirect: str

    @property
    def encoded(self) -> str:
        return get_encoded_creds(self.client_id, self.client_secret)


class GoogleApiCreds(BaseModel):
    client_id: str
    client_secret: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1)

    bot_token: str
    api_id: int
    api_hash: str

    db_string: str

    yt: GoogleApiCreds
    ymusic: OauthCreds

    proxy: str
    root_url: str
    jwt_secret: str


config = Config(_env_file=".env")

__all__ = ["config", "OauthCreds"]
