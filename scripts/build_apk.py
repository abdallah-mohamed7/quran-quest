"""
One-shot APK build + install.
Run from inside quran-quest:  python scripts/build_apk.py

Steps:
  1. Install Capacitor (once)
  2. Prep paths (vite base, audio paths)
  3. Build the web app (npm run build)
  4. Init Capacitor + add Android platform (once)
  5. Sync web assets → android
  6. Build the APK
  7. Install on phone via adb
"""

import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ Run this from inside the quran-quest folder")
    sys.exit(1)

APP_NAME = "Quran Quest"
APP_ID = "com.amaha.quranquest"


def run(cmd: str, cwd: pathlib.Path | None = None, check: bool = True) -> int:
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=str(cwd or ROOT))
    if check and r.returncode != 0:
        print(f"❌ failed: {cmd}")
        sys.exit(1)
    return r.returncode


def exists(path: str) -> bool:
    return (ROOT / path).exists()


# ══════════════════════════════════════════════════════════
# 1. Install Capacitor (only if not already installed)
# ══════════════════════════════════════════════════════════
print("\n═══ 1/7  Install Capacitor ═══")
if not exists("node_modules/@capacitor/core"):
    run("npm install @capacitor/core @capacitor/cli @capacitor/android")
else:
    print("  ⏭  Capacitor already installed")


# ══════════════════════════════════════════════════════════
# 2. Prep paths
# ══════════════════════════════════════════════════════════
print("\n═══ 2/7  Prep paths for Capacitor ═══")

# vite.config.ts — relative base
VC = ROOT / "vite.config.ts"
if VC.exists():
    c = VC.read_text(encoding="utf-8")
    if "base:" not in c:
        shutil.copy2(VC, VC.with_suffix(".ts.bak_apk"))
        c = c.replace(
            "export default defineConfig({",
            "export default defineConfig({\n  base: './',",
            1,
        )
        VC.write_text(c, encoding="utf-8")
        print("  ✅ vite.config.ts — base: './'")
    else:
        print("  ⏭  vite.config.ts already has base")

# QuranAudio — strip leading slash
QA = ROOT / "src/game/systems/QuranAudio.ts"
if QA.exists():
    c = QA.read_text(encoding="utf-8")
    old = "this.el.src = cur.file.startsWith('/') ? cur.file : '/' + cur.file;"
    new = "this.el.src = cur.file.startsWith('/') ? cur.file.slice(1) : cur.file;"
    if old in c:
        shutil.copy2(QA, QA.with_suffix(".ts.bak_apk"))
        QA.write_text(c.replace(old, new, 1), encoding="utf-8")
        print("  ✅ QuranAudio.ts — relative paths")
    else:
        print("  ⏭  QuranAudio.ts already relative")

# index.html — mobile viewport
IH = ROOT / "index.html"
if IH.exists():
    c = IH.read_text(encoding="utf-8")
    if "viewport-fit=cover" not in c:
        shutil.copy2(IH, IH.with_suffix(".html.bak_apk"))
        c = c.replace(
            'content="width=device-width, initial-scale=1.0"',
            'content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"',
        )
        IH.write_text(c, encoding="utf-8")
        print("  ✅ index.html — mobile viewport")


# ══════════════════════════════════════════════════════════
# 3. Build the web app
# ══════════════════════════════════════════════════════════
print("\n═══ 3/7  Build web app ═══")
run("npm run build")

if not (ROOT / "dist" / "index.html").exists():
    print("❌ dist/index.html not created — build failed")
    sys.exit(1)
print("  ✅ dist/ created")


# ══════════════════════════════════════════════════════════
# 4. Init Capacitor + add Android platform (once)
# ══════════════════════════════════════════════════════════
print("\n═══ 4/7  Configure Capacitor ═══")

CONFIG = ROOT / "capacitor.config.ts"
if not CONFIG.exists():
    CONFIG.write_text(f'''import type {{ CapacitorConfig }} from '@capacitor/cli';

const config: CapacitorConfig = {{
  appId: '{APP_ID}',
  appName: '{APP_NAME}',
  webDir: 'dist',
  android: {{
    allowMixedContent: true,
  }},
}};

export default config;
''', encoding="utf-8")
    print("  ✅ capacitor.config.ts created")
else:
    print("  ⏭  capacitor.config.ts exists")

if not (ROOT / "android").exists():
    run("npx cap add android")
else:
    print("  ⏭  android/ folder exists")


# ══════════════════════════════════════════════════════════
# 5. Sync web assets → android
# ══════════════════════════════════════════════════════════
print("\n═══ 5/7  Sync web assets → android ═══")
run("npx cap sync android")


# ══════════════════════════════════════════════════════════
# 6. Build the APK
# ══════════════════════════════════════════════════════════
print("\n═══ 6/7  Build APK (gradle) ═══")
gradlew = "gradlew.bat" if sys.platform.startswith("win") else "./gradlew"
run(f"{gradlew} assembleDebug", cwd=ROOT / "android")

APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
if not APK.exists():
    print(f"❌ APK not created at {APK}")
    print("   Check the gradle output above for errors.")
    sys.exit(1)

size_mb = APK.stat().st_size / (1024 * 1024)
print(f"  ✅ APK built: {APK} ({size_mb:.1f} MB)")


# ══════════════════════════════════════════════════════════
# 7. Install on phone via adb
# ══════════════════════════════════════════════════════════
print("\n═══ 7/7  Install on phone ═══")

# Check a device is connected
r = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if l and "List" not in l]
if not lines:
    print("⚠  No phone detected by adb.")
    print(f"   Connect the phone via USB with USB debugging enabled,")
    print(f"   then manually install: {APK}")
    sys.exit(0)

print(f"  Device(s): {lines}")

# Install
r = subprocess.run(
    f'adb install -r "{APK}"',
    shell=True, capture_output=True, text=True,
)
print(r.stdout.strip())
if "Success" in r.stdout:
    print(f"\n🎉 Installed! Look for '{APP_NAME}' on your phone's app drawer.")
else:
    print("❌ adb install failed — see message above.")
    print(f"   Manual fallback: adb install -r \"{APK}\"")

print("\n" + "=" * 55)
print("Done.")
print("=" * 55)
print(f"""
Rebuild after changes:
  npm run build && npx cap sync android && cd android && gradlew assembleDebug && cd .. && adb install -r android\\app\\build\\outputs\\apk\\debug\\app-debug.apk

Or just re-run this script: python scripts/build_apk.py
""")