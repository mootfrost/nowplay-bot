from app.MusicProvider.Strategy import MusicProviderStrategy
from app.models import Track


class MusicProviderContext:
    def __init__(self, strategy: MusicProviderStrategy):
        self.strategy = strategy

    @property
    def strategy(self) -> MusicProviderStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: MusicProviderStrategy) -> None:
        self._strategy = strategy

    async def get_tracks(self) -> list[Track]:
        token = await self.strategy.handle_token()
        return await self.strategy.get_tracks(token)

    async def get_cached_track(self, track: Track):
        res = await self.strategy.fetch_track(track)
        if not res:
            return track
        return res