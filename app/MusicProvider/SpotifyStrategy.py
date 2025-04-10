import asyncio
import time

import aiohttp

from app.config import config
from app.MusicProvider.Strategy import MusicProviderStrategy
from app.dependencies import get_session_context
from sqlalchemy import select, update

from app.models import User, Track
from app.MusicProvider.auth import refresh_token, get_oauth_creds


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

        if int(time.time()) < user.spotify_auth['refresh_at']:
            return user.spotify_auth['access_token']

        token, expires_in = await refresh_token('https://accounts.spotify.com/api/token',
                                                user.spotify_auth['refresh_token'],
                                                config.spotify.encoded
                                                )
        async with get_session_context() as session:
            await session.execute(
                update(User).where(User.id == self.user_id).values(spotify_auth=get_oauth_creds(token,
                                                                                                user.spotify_auth['refresh_token'],
                                                                                                expires_in))
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
            if resp.status != 200:
                return None
            return await resp.json()

    @staticmethod
    def convert_track(track: dict):
        if track['type'] != 'track':
            return None

        return Track(
            name=track['name'],
            artist=', '.join(x['name'] for x in track['artists']),
            cover_url=track['album']['images'][0]['url'],
            spotify_id=track['id']
        )

    async def get_tracks(self, token) -> list[Track]:
        current, recent = await asyncio.gather(
            self.request('/me/player/currently-playing', token),
            self.request('/me/player/recently-played', token)
        )
        tracks = []
        if current:
            tracks.append(self.convert_track(current['item']))
        for item in recent['items']:
            tracks.append(self.convert_track(item['track']))

        tracks = [x for x in tracks if x]
        tracks = list(dict.fromkeys(tracks))
        print(tracks)
        return tracks

    async def fetch_track(self, track: Track):
        async with get_session_context() as session:
            resp = await session.execute(
                select(Track).where(Track.spotify_id == track.spotify_id)
            )
        return resp.scalars().first()

    def song_link(self, track: Track):
        return f'<a href="https://open.spotify.com/track/{track.spotify_id}">Spotify</a> | <a href="https://song.link/s/{track.spotify_id}">Other</a>'

    def track_id(self, track: Track):
        return track.spotify_id


__all__ = ['SpotifyStrategy']
