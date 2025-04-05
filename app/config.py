import base64

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class SpotifyCreds(BaseModel):
    client_id: str
    client_secret: str
    redirect: str


class GoogleApiCreds(BaseModel):
    client_id: str
    client_secret: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='_',
                                      env_nested_max_split=1)
    bot_token: str
    api_id: int
    api_hash: str
    db_string: str
    spotify: SpotifyCreds
    yt: GoogleApiCreds
    proxy: str = ''
    jwt_secret: str


config = Config(_env_file='.env')
spotify_creds = base64.b64encode(config.spotify.client_id.encode() + b':' + config.spotify.client_secret.encode()).decode("utf-8")

__all__ = ['config', 'spotify_creds']