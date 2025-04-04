from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

# Open MP3 file
audio = MP3("empty.mp3", ID3=ID3)

# Check if APIC (cover art) exists
cover_art = audio.tags.getall("APIC")
if cover_art:
    print("✅ Cover art is embedded successfully.")
else:
    print("❌ Cover art is missing!")