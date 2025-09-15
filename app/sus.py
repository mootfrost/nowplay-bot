from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from yandex_music import Client

client = Client("").init()
print(client.queues_list())

queues = client.tracks(19801159)
print(queues)
# Последняя проигрываемая очередь всегда в начале списка
last_queue = client.queue(queues[0].id)

last_track_id = last_queue.get_current_track()
last_track = last_track_id.fetch_track()

artists = ", ".join(last_track.artists_name())
title = last_track.title
print(f"Сейчас играет: {artists} - {title}")

try:
    lyrics = last_track.get_lyrics("LRC")
    print(lyrics.fetch_lyrics())

    print(f"\nИсточник: {lyrics.major.pretty_name}")
except NotFoundError:
    print("Текст песни отсутствует")
