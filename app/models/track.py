from typing import Optional

from app.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, LargeBinary, Integer



class Track(Base):
    __tablename__ = 'tracks'
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    telegram_access_hash: Mapped[Optional[int]] = mapped_column(BigInteger)
    telegram_file_reference: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    spotify_id: Mapped[str]
    name: Mapped[str]
    artist: Mapped[str]
    cover_url: Mapped[str]
    used_times: Mapped[str] = mapped_column(Integer, default=1)




__all__ = ['Track']