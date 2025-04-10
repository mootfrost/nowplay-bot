import time

from app import config
from app.MusicProvider.auth import refresh_token, get_oauth_creds
from app.dependencies import get_session_context
from app.models import Track, User
from app.MusicProvider.Strategy import MusicProviderStrategy
from sqlalchemy import select, update
from yandex_music import ClientAsync, TracksList


class YandexMusicStrategy(MusicProviderStrategy):
    async def fetch_track(self, track: Track) -> Track:
        async with get_session_context() as session:
            resp = await session.execute(
                select(Track).where(Track.ymusic_id == track.ymusic_id)
            )
        return resp.scalars().first()

    async def handle_token(self) -> str | None:
        async with get_session_context() as session:
            res = await session.execute(select(User).where(User.id == self.user_id))
            user: User = res.scalars().first()
        if not user:
            return None

        if int(time.time()) < user.ymusic_auth['refresh_at']:
            return user.ymusic_auth['access_token']

        token, expires_in = await refresh_token('https://oauth.yandex.com/token',
                                                user.ymusic_auth['refresh_token'],
                                                config.ymusic.encoded
                                                )
        async with get_session_context() as session:
            await session.execute(
                update(User).where(User.id == self.user_id).values(spotify_auth=get_oauth_creds(token,
                                                                                                user.ymusic_auth['refresh_token'],
                                                                                                expires_in))
            )
            await session.commit()
        return token

    async def get_tracks(self, token) -> list[Track]:
        client = await ClientAsync(token).init()
        liked: TracksList = await client.users_likes_tracks()
        tracks = await client.tracks([x.id for x in liked.tracks[:5]])
        print(tracks[0])
        return [
            Track(
                name=x.title,
                artist=', '.join([art.name for art in x.artists]),
                ymusic_id=x.id,
                cover_url=x.cover_uri
            )
            for x in tracks
        ]

    def song_link(self, track: Track):
        return f'<a href="https://music.yandex.ru/track/{track.ymusic_id}">Yandex music</a> | <a href="https://song.link/ya/{track.ymusic_id}">Other</a>'

    def track_id(self, track: Track):
        return track.ymusic_id
