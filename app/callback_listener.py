from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from telethon import TelegramClient
import aiohttp
import time
import jwt

from app.dependencies import get_session
from app.models.user import User
from config import config, OauthCreds
from app.MusicProvider.auth import get_oauth_creds

client = TelegramClient('nowplaying_callback', config.api_id, config.api_hash)
client.parse_mode = 'html'


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.connect()
    await client.sign_in(bot_token=config.bot_token)
    yield


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory='app/static', html=True), name='static')


class LinkException(Exception):
    pass


@app.exception_handler(LinkException)
async def link_exception_handler(request: Request, exc: LinkException):
    return FileResponse('app/static/error.html', media_type='text/html')


async def code_to_token(code: str, uri: str, creds: OauthCreds) -> tuple[str, str, int]:
    token_headers = {
        "Authorization": "Basic " + creds.encoded,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": creds.redirect
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.post(uri, data=token_data, headers=token_headers)
    resp = await resp.json()
    if 'access_token' not in resp:
        raise LinkException()
    return resp['access_token'], resp['refresh_token'], int(resp['expires_in'])


def get_decoded_id(string: str):
    try:
        return jwt.decode(string, config.jwt_secret, algorithms=['HS256'])['tg_id']
    except:
        raise LinkException()

second_provider_notification = """
\n\nYou just added second service, it will be used as default.
If you want to use other one time just type <b>y for Yandex music</b>. or <b>s for Spotify</b>. 
You can change default service using /default command.
"""


@app.get('/spotify_callback')
async def spotify_callback(code: str, state: str, session: AsyncSession = Depends(get_session)):
    user_id = get_decoded_id(state)
    token, refresh_token, expires_in = await code_to_token(code, 'https://accounts.spotify.com/api/token', config.spotify)
    creds = get_oauth_creds(token, refresh_token, expires_in)
    user = await session.get(User, user_id)
    if user:
        user.spotify_auth = creds
        user.default = 'spotify'
    else:
        user = User(id=user_id,
                    spotify_auth=creds,
                    default='spotify'
                    )
        session.add(user)
    await session.commit()
    reply = "Account linked!"
    if user.spotify_auth:
        reply += second_provider_notification
    await client.send_message(user_id, reply)
    return FileResponse('app/static/success.html', media_type='text/html')



@app.get('/ym_callback')
async def ym_callback(state: str, code: str, cid: str, session: AsyncSession = Depends(get_session)):
    user_id = get_decoded_id(state)
    token, refresh_token, expires_in = await code_to_token(code, 'https://oauth.yandex.com/token', config.ymusic)
    creds = get_oauth_creds(token, refresh_token, expires_in)
    user = await session.get(User, user_id)
    if user:
        user.ymusic_auth = creds
        user.default = 'ymusic'
    else:
        user = User(id=user_id,
                    ymusic_auth=creds,
                    default='ymusic'
                    )
        session.add(user)
    await session.commit()
    reply = "Account linked! Note, that currently bot only allows to share tracks from Liked playlist."
    if user.spotify_auth:
        reply += second_provider_notification
    await client.send_message(user_id, reply)
    return FileResponse('app/static/success.html', media_type='text/html')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
