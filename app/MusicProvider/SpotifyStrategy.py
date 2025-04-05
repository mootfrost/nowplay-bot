import asyncio
import base64
import time

import aiohttp

from app.config import config, spotify_creds
from app.MusicProvider.Strategy import MusicProviderStrategy
from app.dependencies import get_session, get_session_context
from sqlalchemy import select, update

from app.models import User, Track


def convert_track(track: dict):
    if track['type'] != 'track':
        return None

    return Track(
        name=track['name'],
        artist=', '.join(x['name'] for x in track['artists']),
        cover_url=track['album']['images'][0]['url'],
        spotify_id=track['id']
    )


async def refresh_token(refresh_token):
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        'Authorization': 'Basic ' + spotify_creds
    }
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    resp = await resp.json()
    return resp['access_token'], resp['expires_in']


class SpotifyStrategy(MusicProviderStrategy):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.token = None

    async def handle_token(self):
        async with get_session_context() as session:
            res = await session.execute(select(User).where(User.id == self.user_id))
            user: User = res.scalars().first()
        if not user:
            return None

        if int(time.time()) < user.spotify_refresh_at:
            return user.spotify_access_token

        token, expires_in = await refresh_token(user.spotify_refresh_token)
        async with get_session_context() as session:
            await session.execute(
                update(User).where(User.id == self.user_id).values(spotify_access_token=token,
                                                                   spotify_refresh_at=int(time.time()) + int(expires_in))
            )
            await session.commit()
        return token

    async def request(self, endpoint, token):
        user_headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            resp = await session.get(f'https://api.spotify.com/v1{endpoint}', headers=user_headers)
            return await resp.json()

    async def get_tracks(self, token) -> list[Track]:
        current, recent = await asyncio.gather(
            self.request('/me/player/currently-playing', token),
            self.request('/me/player/recently-played', token)
        )
        tracks = []
        if current:
            tracks.append(convert_track(current['item']))
        for item in recent['items']:
            tracks.append(convert_track(item['track']))

        tracks = [x for x in tracks if x]
        return tracks

    async def fetch_track(self, track: Track):
        async with get_session_context() as session:
            resp = await session.execute(
                select(Track).where(Track.spotify_id == track.spotify_id)
            )
        return resp.scalars().first()


__all__ = ['SpotifyStrategy']
