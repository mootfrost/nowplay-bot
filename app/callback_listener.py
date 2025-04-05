from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from telethon import TelegramClient
import aiohttp
import time
import jwt

from app.dependencies import get_session
from app.models.user import User
from config import config, spotify_creds

client = TelegramClient('nowplaying_callback', config.api_id, config.api_hash)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.connect()
    await client.sign_in(bot_token=config.bot_token)
    yield


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory='static', html=True), name='static')


class LinkException(Exception):
    pass


@app.exception_handler(LinkException)
async def unicorn_exception_handler(request: Request, exc: LinkException):
    return FileResponse('static/error.html', status_code=400)


async def get_spotify_token(code: str):
    token_headers = {
        "Authorization": "Basic " + spotify_creds,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.spotify.redirect
    }

    async with aiohttp.ClientSession() as session:
        resp = await session.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    resp = await resp.json()

    if 'access_token' not in resp:
        raise LinkException()
    return resp['access_token'], resp['refresh_token'], int(resp['expires_in'])


@app.get('/spotify_callback')
async def spotify_callback(code: str, state: str, session: AsyncSession = Depends(get_session)):
    try:
        user_id = jwt.decode(state, config.jwt_secret, algorithms=['HS256'])['tg_id']
    except:
        raise LinkException()


    token, refresh_token, expires_in = await get_spotify_token(code)
    user = await session.get(User, user_id)
    if user:
        user.spotify_access_token = token
        user.spotify_refresh_token = refresh_token
        user.spotify_refreshed_at = int(time.time())
    else:
        user = User(id=user_id,
                    spotify_access_token=token,
                    spotify_refresh_token=refresh_token,
                    spotify_refresh_at=int(time.time()) + expires_in
                    )
        session.add(user)
    await session.commit()
    await client.send_message(user_id, "Account linked!")
    return FileResponse('static/success.html', media_type='text/html')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
