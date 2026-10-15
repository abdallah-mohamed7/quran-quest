"""If 001.mp3 actually contains page 604's audio, this maps
001<->604, 002<->603, ... so file NNN.mp3 = mushaf page NNN."""
import pathlib

SRC = pathlib.Path(r"C:\Users\amaha\Desktop\my pc\النجاه\الشيخ الحصري")

# Sanity check first
files = sorted(SRC.glob("*.mp3"))
print(f"Found {len(files)} mp3 files")
assert len(files) == 604, f"Expected 604, got {len(files)}"

# Rename through a temp name so we don't overwrite
for i in range(1, 605):
    src = SRC / f"{i:03d}.mp3"
    tmp = SRC / f"__tmp_{i:03d}.mp3"
    if src.exists():
        src.rename(tmp)

for i in range(1, 605):
    tmp = SRC / f"__tmp_{i:03d}.mp3"
    dst = SRC / f"{605 - i:03d}.mp3"
    if tmp.exists():
        tmp.rename(dst)

print("✅ Reversed. Now 001.mp3 = page 1.")