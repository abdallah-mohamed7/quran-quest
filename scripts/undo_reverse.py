"""Swap reversed page audio back to normal.
After running: 001.mp3 = page 1, 604.mp3 = page 604."""

import pathlib

# Both places need fixing:
SRC = pathlib.Path(r"C:\Users\amaha\Desktop\my pc\النجاه\الشيخ الحصري")
DST = pathlib.Path("public/quran/audio/pages")

for base in (SRC, DST):
    if not base.exists():
        print(f"⚠  skip (missing): {base}")
        continue

    files = sorted(base.glob("[0-9][0-9][0-9].mp3"))
    print(f"\n{base}")
    print(f"  found {len(files)} files")

    # Phase 1: rename everything to a temp name
    for i in range(1, 605):
        src = base / f"{i:03d}.mp3"
        tmp = base / f"__swap_{i:03d}.mp3"
        if src.exists():
            src.rename(tmp)

    # Phase 2: temp -> final swapped name
    for i in range(1, 605):
        tmp = base / f"__swap_{i:03d}.mp3"
        dst = base / f"{605 - i:03d}.mp3"
        if tmp.exists():
            tmp.rename(dst)

print("\n✅ Done.")
print("  001.mp3 is now page 1 (Al-Fatiha)")
print("  604.mp3 is now page 604 (An-Nas)")