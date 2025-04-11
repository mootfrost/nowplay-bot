import base64

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class OauthCreds(BaseModel):
    client_id: str
    client_secret: str
    redirect: str

    @property
    def encoded(self) -> str:
        return base64.b64encode(self.client_id.encode() + b':' + self.client_secret.encode()).decode("utf-8")


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
    spotify: OauthCreds
    yt: GoogleApiCreds
    ymusic: OauthCreds

    proxy: str | None
    jwt_secret: str


config = Config(_env_file='.env')

__all__ = ['config', 'OauthCreds']
