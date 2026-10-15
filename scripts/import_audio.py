"""Copy page MP3s into public/quran/audio/pages/001.mp3 ... 604.mp3"""
import pathlib
import shutil
import re

SRC = pathlib.Path(r"C:\Users\amaha\Desktop\my pc\النجاه\الشيخ الحصري")
DST = pathlib.Path("public/quran/audio/pages")
DST.mkdir(parents=True, exist_ok=True)

NUM = re.compile(r"^(\d{1,3})\.mp3$", re.IGNORECASE)

copied, skipped, bad = 0, 0, []

for f in sorted(SRC.iterdir()):
    if not f.is_file():
        continue
    m = NUM.match(f.name)
    if not m:
        bad.append(f.name)
        continue
    page = int(m.group(1))
    if not (1 <= page <= 604):
        bad.append(f.name)
        continue
    target = DST / f"{page:03d}.mp3"
    if target.exists():
        skipped += 1
        continue
    shutil.copy2(f, target)
    copied += 1
    if copied % 50 == 0:
        print(f"  copied {copied}...")

print(f"\n✅ Copied:  {copied}")
print(f"⏭  Skipped: {skipped}")
if bad:
    print(f"\n⚠️  Didn't match: {bad[:10]}")