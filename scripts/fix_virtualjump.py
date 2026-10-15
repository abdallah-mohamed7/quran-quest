"""Remove the unused virtualJump field. Touch jump still works via jumpQueuedAt."""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ run from inside quran-quest")
    sys.exit(1)

LS = ROOT / "src" / "game" / "scenes" / "LevelScene.ts"
if not LS.exists():
    print("❌ LevelScene.ts not found")
    sys.exit(1)

c = LS.read_text(encoding="utf-8")

# Backup once
bak = LS.with_suffix(".ts.bak_vj2")
if not bak.exists():
    shutil.copy2(LS, bak)
    print(f"  💾 {bak.name}")

# Count occurrences
before = c.count("virtualJump")

# Remove every line that mentions virtualJump
lines = c.split("\n")
kept = [l for l in lines if "virtualJump" not in l]
c2 = "\n".join(kept)

after = c2.count("virtualJump")

if before == after:
    print("  ⏭  no virtualJump references found")
    sys.exit(0)

LS.write_text(c2, encoding="utf-8")
print(f"  ✅ removed {before - after} line(s) mentioning virtualJump")
print(f"     (touch jump still works via jumpQueuedAt)")

print("\n✅ Done. Now run:")
print("  npm run build")