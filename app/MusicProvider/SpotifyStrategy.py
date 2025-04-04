import base64
import time

import aiohttp

from app.config import config
from app.MusicProvider.Strategy import MusicProviderStrategy
from app.dependencies import get_session, get_session_context
from sqlalchemy import select, update

from app.models import User, Track


creds = base64.b64encode(config.spotify.client_id.encode() + b':' + config.spotify.client_secret.encode()).decode("utf-8")


class SpotifyStrategy(MusicProviderStrategy):
    async def handle_token(self):
        async with get_session_context() as session:
            res = await session.execute(select(User).where(User.id == self.user_id))
            user: User = res.scalars().first()
        if not user:
            return None

        if int(time.time()) < user.spotify_refresh_at:
            return user.spotify_access_token

        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            'Authorization': 'Basic ' + creds
        }
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": user.spotify_refresh_token
        }
        async with aiohttp.ClientSession() as session:
            resp = await session.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
        resp = await resp.json()
        token, expires_in = resp['access_token'], resp['expires_in']
        async with get_session_context() as session:
            await session.execute(
                update(User).where(User.id == self.user_id).values(spotify_access_token=token,
                                                                   spotify_refresh_at=int(time.time()) + int(expires_in)
                                                                   )
            )
            await session.commit()
        return token

    async def get_tracks(self, token) -> list[Track]:
        user_headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        user_params = {
            'limit': 1
        }
        res = []
        async with aiohttp.ClientSession() as session:
            resp = await session.get('https://api.spotify.com/v1/me/player/recently-played', params=user_params, headers=user_headers)
            data = await resp.json()
            for i, el in enumerate(data['items']):
                track = el['track']
                resp = await session.get(f'https://api.spotify.com/v1/albums/{track['album']['id']}', headers=user_headers)
                album = await resp.json()
                cover = album['images'][0]
                res.append(Track(
                    name=track['name'],
                    artist=', '.join(x['name'] for x in track['artists']),
                    cover_url=cover['url'],
                    spotify_id=track['id']
                ))
        return res

    async def fetch_track(self, track: Track):
        async with get_session_context() as session:
            resp = await session.execute(
                select(Track).where(Track.spotify_id == track.spotify_id)
            )
        return resp.scalars().first()