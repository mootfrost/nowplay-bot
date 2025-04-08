from app.dependencies import get_session_context
from app.models import Track, User
from app.MusicProvider.Strategy import MusicProviderStrategy
from sqlalchemy import select
from yandex_music import ClientAsync, TracksList


class YandexMusicStrategy(MusicProviderStrategy):
    async def fetch_track(self, track: Track) -> Track:
        async with get_session_context() as session:
            resp = await session.execute(
                select(Track).where(Track.ymusic_id == track.ymusic_id)
            )
        return resp.scalars().first()

    async def handle_token(self) -> str:
        async with get_session_context() as session:
            res = await session.execute(select(User).where(User.id == self.user_id))
            user: User = res.scalars().first()
        if not user:
            return None
        return user.ymusic_token

    async def get_tracks(self, token) -> list[Track]:
        client = await ClientAsync(token).init()
        liked: TracksList = await client.users_likes_tracks()
        tracks = await client.tracks([x.id for x in liked.tracks[:5]])
        return [
            Track(
                name=x.title,
                artist=', '.join([art.name for art in x.artists]),
                ymusic_id=x.id,
                cover_url=x.cover_uri
            )
            for x in tracks
        ]
