"""Download per-ayah MP3s for 10 short surahs (Juz 30).
Total ~3 MB. Replaces the 1.5 GB page audio."""
import pathlib
import requests

# Everyayah.com folders — try one of these if 404:
#   Husary_128kbps | Husary_Mujawwad_64kbps | Husary_128kbps_Improve
#   Alafasy_128kbps | Abdul_Basit_Murattal_192kbps | Minshawy_Murattal_128kbps
RECITER = "Husary_128kbps"
BASE = f"https://everyayah.com/data/{RECITER}"

OUT = pathlib.Path("public/quran/audio/surahs")
OUT.mkdir(parents=True, exist_ok=True)

# (surah_number, ayah_count)
SURAHS = [
    (105, 5),   # Al-Fil
    (106, 4),   # Quraysh
    (107, 7),   # Al-Ma'un
    (108, 3),   # Al-Kawthar
    (109, 6),   # Al-Kafirun
    (110, 3),   # An-Nasr
    (111, 5),   # Al-Masad
    (112, 4),   # Al-Ikhlas
    (113, 5),   # Al-Falaq
    (114, 6),   # An-Nas
]

session = requests.Session()
total_mb = 0.0
for surah, count in SURAHS:
    surah_dir = OUT / f"{surah:03d}"
    surah_dir.mkdir(exist_ok=True)
    for ayah in range(1, count + 1):
        name = f"{surah:03d}{ayah:03d}.mp3"
        dest = surah_dir / f"{ayah:03d}.mp3"
        if dest.exists():
            continue
        url = f"{BASE}/{name}"
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            print(f"  ⚠  {name} → {r.status_code}")
            continue
        dest.write_bytes(r.content)
        mb = len(r.content) / 1024 / 1024
        total_mb += mb
        print(f"  ✅ {surah:03d}/{ayah:03d}.mp3  {mb*1024:.0f} KB")

print(f"\n✅ Total: {total_mb:.1f} MB")
print(f"Files in: {OUT.resolve()}")