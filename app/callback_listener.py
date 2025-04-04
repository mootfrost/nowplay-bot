from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse
import uvicorn
from telethon import TelegramClient
import base64
import aiohttp
import time

from app.dependencies import get_session
from app.models.user import User
from config import config

client = TelegramClient('nowplaying_callback', config.api_id, config.api_hash)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global r
    await client.connect()
    await client.sign_in(bot_token=config.bot_token)
    yield


app = FastAPI(lifespan=lifespan)
creds = base64.b64encode(config.spotify.client_id.encode() + b':' + config.spotify.client_secret.encode()).decode(
    "utf-8")


async def get_spotify_token(code: str, user_id: int):
    token_headers = {
        "Authorization": "Basic " + creds,
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

    return resp['access_token'], resp['refresh_token'], int(resp['expires_in'])


def generate_success_reponse():
    content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #ffffff;
            font-family: 'Poppins', sans-serif;
            text-align: center;
            color: #000;
        }
        img {
            max-width: 120px;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 28px;
            font-weight: 600;
            color: #000;
            margin-bottom: 10px;
        }
        p {
            font-size: 18px;
            font-weight: 400;
            opacity: 0.7;
        }
    </style>
</head>
<body>
<h1>@nowlisten bot</h1>
<h1>Success! Now you can return to the bot</h1>
</body>
</html>"""
    return HTMLResponse(content=content)


@app.get('/spotify_callback')
async def spotify_callback(code: str, state: str, session: AsyncSession = Depends(get_session)):
    user_id = int(state.replace('tg_', ''))
    token, refresh_token, expires_in = await get_spotify_token(code, user_id)
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
    return generate_success_reponse()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
