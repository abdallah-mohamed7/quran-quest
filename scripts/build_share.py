"""Build a shareable APK and copy it to the Desktop."""

import pathlib
import shutil
import subprocess
import sys
import time

PROJECT = pathlib.Path(r"C:\Users\amaha\quran-quest")
DESKTOP = pathlib.Path.home() / "Desktop"

if not (PROJECT / "package.json").exists():
    print("X  run from inside quran-quest")
    sys.exit(1)


def run(cmd, cwd=PROJECT, check=True):
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=str(cwd))
    if check and r.returncode != 0:
        print(f"X  failed: {cmd}")
        sys.exit(1)
    return r


# ── 1. Clean old build ─────────────────────────────────
print("=" * 55)
print("  1/5  Clean old build")
print("=" * 55)
for d in ["dist", "android/app/build"]:
    p = PROJECT / d
    if p.exists():
        shutil.rmtree(p)
        print(f"  removed {d}")

# ── 2. Build web ───────────────────────────────────────
print("\n" + "=" * 55)
print("  2/5  Build web app")
print("=" * 55)
run("npm run build")

if not (PROJECT / "dist" / "index.html").exists():
    print("X  dist/index.html missing")
    sys.exit(1)
print("  ✅ dist/ built")

# ── 3. Sync to Android ─────────────────────────────────
print("\n" + "=" * 55)
print("  3/5  Sync to Android")
print("=" * 55)
run("npx cap sync android")

# ── 4. Build APK ───────────────────────────────────────
print("\n" + "=" * 55)
print("  4/5  Build APK (this takes 30-90 seconds)")
print("=" * 55)
gradlew = "gradlew.bat" if sys.platform.startswith("win") else "./gradlew"
run(f"{gradlew} assembleDebug", cwd=PROJECT / "android")

APK = PROJECT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
if not APK.exists():
    print(f"X  APK not found at {APK}")
    sys.exit(1)

size_mb = APK.stat().st_size / (1024 * 1024)
print(f"  ✅ APK built: {size_mb:.1f} MB")

# ── 5. Copy to Desktop with clean name ─────────────────
print("\n" + "=" * 55)
print("  5/5  Copy to Desktop")
print("=" * 55)

date = time.strftime("%Y-%m-%d")
friendly_name = f"Quran-Quest-{date}.apk"
dest = DESKTOP / friendly_name
shutil.copy2(APK, dest)

print(f"  ✅ Copied to: {dest}")
print(f"     Size: {size_mb:.1f} MB")

# ── Done ───────────────────────────────────────────────
print("\n" + "=" * 55)
print("  ✅ READY TO SHARE")
print("=" * 55)
print(f"""
APK:  {dest}

Share this file with your family:
  • WhatsApp — drag the .apk into a chat
  • USB — copy to phone's Downloads folder, tap to install
  • Google Drive — upload, share the link
  • Email — attach if under 25 MB

On their phone, when installing:
  • Android will warn "unknown source"
  • Tap "Install anyway" / "Allow from this source"
  • It works — that's normal for apps not on the Play Store
""")