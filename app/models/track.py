from typing import Optional

from app.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, LargeBinary, Integer, JSON


class Track(Base):
    __tablename__ = 'tracks'
    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_reference: Mapped[Optional[dict]] = mapped_column(JSON)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    telegram_access_hash: Mapped[Optional[int]] = mapped_column(BigInteger)
    telegram_file_reference: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    yt_id: Mapped[Optional[str]]

    spotify_id: Mapped[Optional[str]]
    ymusic_id: Mapped[Optional[str]]

    name: Mapped[str]
    artist: Mapped[str]
    cover_url: Mapped[str]
    used_times: Mapped[int] = mapped_column(Integer, default=1)

    def __hash__(self):
        return hash(self.spotify_id)

    def __eq__(self, other):
        if not isinstance(other, Track):
            return NotImplemented
        return self.spotify_id == other.spotify_id



__all__ = ['Track']