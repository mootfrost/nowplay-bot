import asyncio
import functools
import io
import time

import aiohttp
from telethon import TelegramClient, events, Button
from telethon.tl.types import (
    UpdateBotInlineSend,
    TypeInputFile,
    DocumentAttributeAudio,
    InputPeerSelf, InputDocument
)
from telethon.tl.custom import InlineBuilder
from telethon import functions
from telethon.utils import get_input_document
import urllib.parse
from mutagen.id3 import ID3, APIC
import logging
from cachetools import LRUCache
from sqlalchemy import select, update
import jwt


from app.MusicProvider import MusicProviderContext, SpotifyStrategy, YandexMusicStrategy
from app.config import config
from app.dependencies import get_session, get_session_context
from app.models import Track, User
from app.youtube_api import name_to_youtube, download_youtube

logging.basicConfig(
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = TelegramClient('nowplaying', config.api_id, config.api_hash)
client.parse_mode = 'html'
cache = LRUCache(maxsize=100)


async def get_user(user_id):
    async with get_session_context() as session:
        return await session.scalar(select(User).where(User.id == user_id))


def get_spotify_link(user_id) -> str:
    params = {
        'client_id': config.spotify.client_id,
        'response_type': 'code',
        'redirect_uri': config.spotify.redirect,
        'scope': 'user-read-recently-played user-read-currently-playing',
        'state': user_id
    }
    return f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"


def get_ymusic_link(user_id) -> str:
    params = {
        'response_type': 'code',
        'client_id': config.ymusic.client_id,
        'state': user_id
    }
    return f"https://oauth.yandex.ru/authorize?{urllib.parse.urlencode(params)}"


@client.on(events.NewMessage(pattern='/start'))
async def start(e: events.NewMessage.Event):
    payload = {
        'tg_id': e.chat_id,
        'exp': int(time.time()) + 300
    }
    enc_user_id = jwt.encode(payload, config.jwt_secret, algorithm='HS256')
    buttons = [
        Button.url('Link Spotify', get_spotify_link(enc_user_id)),
        Button.url('Link Yandex music', get_ymusic_link(enc_user_id)),
    ]
    await e.respond("Hi! I can help you share music you listen on Spotify or Yandex muisc\n\nPress button below to authorize your account first",
                    buttons=buttons)


@client.on(events.NewMessage(pattern='/default'))
async def change_default(e: events.NewMessage.Event):
    user = await get_user(e.chat_id)
    if not user:
        return await e.respond('Please link your account first')
    buttons = []
    if user.spotify_auth:
        buttons.append(Button.inline('Spotify', 'default_spotify'))
    if user.ymusic_auth:
        buttons.append(Button.inline('Yandex music', 'default_ymusic'))

    await e.respond('Select service you want to use as default', buttons=buttons)


@client.on(events.CallbackQuery(pattern='default_*'))
async def set_default(e: events.CallbackQuery.Event):
    async with get_session_context() as session:
        await session.execute(
            update(User).where(User.id == e.sender_id).values(default=str(e.data).split('_')[1])
        )
        await session.commit()
    await e.respond('Default service updated')


async def fetch_file(url) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()


# TODO: make faster and somehow fix cover not displaying in response
async def update_dummy_file_cover(cover_url: str):
    cover = await fetch_file(cover_url)
    dummy_name = 'empty.mp3'
    audio = ID3(dummy_name)
    audio.delall('APIC')
    audio.add(APIC(
        encoding=3,
        mime='image/jpeg',
        type=3,
        desc='Cover',
        data=cover
    ))
    res = io.BytesIO()
    audio.save(res)
    dummy_file = await client.upload_file(res.getvalue(), file_name='empty.mp3')


async def build_response(track: Track, track_id: str, links: str):
    if not track.telegram_id:
        dummy_file = await client.upload_file('empty.mp3')
        buttons = [Button.inline('Loading', 'loading')]
    else:
        dummy_file = InputDocument(
            id=track.telegram_id,
            access_hash=track.telegram_access_hash,
            file_reference=track.telegram_file_reference
        )
        buttons = None
    return await InlineBuilder(client).document(
        file=dummy_file,
        title=track.name,
        description=track.artist,
        id=track_id,
        mime_type='audio/mpeg',
        attributes=[
            DocumentAttributeAudio(
                duration=1,
                voice=False,
                title=track.name,
                performer=track.artist,
                waveform=None,
            )
        ],
        text=links,
        buttons=buttons
    )


@client.on(events.InlineQuery())
async def query_list(e: events.InlineQuery.Event):
    user = await get_user(e.sender_id)
    if not user:
        return await e.answer(switch_pm='Link account first', switch_pm_param='link')
    if user.default == 'spotify' and user.spotify_auth:
        ctx = MusicProviderContext(SpotifyStrategy(e.sender_id))
    else:
        ctx = MusicProviderContext(YandexMusicStrategy(e.sender_id))
    tracks = (await ctx.get_tracks())[:5]
    result = []

    for track in tracks:
        track = await ctx.get_cached_track(track)
        music_id = ctx.strategy.track_id(track)
        cache[music_id] = track
        result.append(await build_response(track, music_id, ctx.strategy.song_link(track)))
    await e.answer(result)


async def track_to_file(track):
    audio, duration = await download_youtube(track.yt_id)
    _, media, _ = await client._file_to_media(
        audio,
        attributes=[
            DocumentAttributeAudio(
                duration=duration,
                voice=False,
                title=track.name,
                performer=track.artist,
                waveform=None,
            )]
    )
    uploaded_media = await client(
        functions.messages.UploadMediaRequest(
            InputPeerSelf(), media=media
        )
    )

    return get_input_document(uploaded_media.document)


async def cache_file(track):
    async with get_session_context() as session:
        session.add(track)
        await session.commit()


async def download_track(track):
    yt_id = await asyncio.get_event_loop().run_in_executor(
        None, functools.partial(name_to_youtube, f'{track.name} - {track.artist}')
    )
    track.yt_id = yt_id
    async with get_session_context() as session:
        existing = await session.scalar(
            select(Track).where(Track.yt_id == yt_id)
        )

        if existing and existing.telegram_id:
            updated = False
            if not existing.spotify_id and track.spotify_id:
                existing.spotify_id = track.spotify_id
                updated = True
            if not existing.ymusic_id and track.ymusic_id:
                existing.ymusic_id = track.ymusic_id
                updated = True
            if updated:
                await session.commit()

            return InputDocument(
                id=existing.telegram_id,
                access_hash=existing.telegram_access_hash,
                file_reference=existing.telegram_file_reference
            )

    file = await track_to_file(track)
    track.telegram_id = file.id
    track.telegram_access_hash = file.access_hash
    track.telegram_file_reference = file.file_reference
    await cache_file(track)
    return file


@client.on(events.Raw([UpdateBotInlineSend]))
async def send_track(e: UpdateBotInlineSend):
    track = cache[e.id]
    if track.telegram_id:
        return

    file = await download_track(track)
    await client.edit_message(e.msg_id, file=file)


async def main():
    await client.start(bot_token=config.bot_token)
    logger.info('Bot started')
    await client.run_until_disconnected()


__all__ = ['main']