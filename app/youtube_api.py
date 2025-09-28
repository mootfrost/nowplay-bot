import asyncio
import functools
import os
from io import BytesIO
from tempfile import TemporaryDirectory
from ytmusicapi import YTMusic, OAuthCredentials
from yt_dlp import YoutubeDL

from app.config import config

# ytmusic = YTMusic(
#     "oauth.json",
#     oauth_credentials=OAuthCredentials(
#         client_id=config.yt.client_id, client_secret=config.yt.client_secret
#     ),
# )
ytmusic = YTMusic()
# if config.proxy:
#     ytmusic.proxies = {'http': config.proxy, 'https': config.proxy}


def name_to_youtube(name: str):
    results = ytmusic.search(name, "songs", limit=10)
    print(results)
    return results[0]["videoId"]


def _download(yt_id: str, directory: str):
    params = {
        "format": "bestaudio",
        "quiet": True,
        "outtmpl": os.path.join(directory, "dl.%(ext)s"),
    }
    if config.proxy:
        params["proxy"] = config.proxy
    with YoutubeDL(params) as ydl:
        return ydl.extract_info(yt_id)


async def download_youtube(yt_id: str) -> tuple[BytesIO, int]:
    with TemporaryDirectory() as tmpdir:
        info = await asyncio.get_event_loop().run_in_executor(
            None, functools.partial(_download, yt_id, tmpdir)
        )
        duration = info["duration"]
        files = os.listdir(tmpdir)
        assert len(files) == 1
        fn = os.path.join(tmpdir, files[0])
        fn2 = os.path.join(tmpdir, "audio.mp3")
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            fn,
            fn2,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        assert proc.returncode == 0
        with open(fn2, "rb") as f:
            res = BytesIO(f.read())
        res.name = os.path.basename(fn2)
        return res, duration
