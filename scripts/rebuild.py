"""Rebuild APK after code changes. Run: python scripts/rebuild.py"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("X  Run this from inside quran-quest")
    sys.exit(1)


def run(cmd: str, cwd: pathlib.Path = ROOT, check: bool = True) -> int:
    print(f"\n$ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=str(cwd))
    if check and r.returncode != 0:
        print(f"\nX  Failed: {cmd}")
        sys.exit(r.returncode)
    return r.returncode


# ── 1. Type-check + build web ────────────────────────
print("═" * 55)
print("  1/5  Build web app")
print("═" * 55)
run("npm run build")

dist = ROOT / "dist" / "index.html"
if not dist.exists():
    print("X  dist/index.html missing — build failed")
    sys.exit(1)
print("  ✅ dist/ built")


# ── 2. Sync to Android ───────────────────────────────
print("\n" + "═" * 55)
print("  2/5  Sync to Android")
print("═" * 55)

if not (ROOT / "android").exists():
    print("  ⚠  android/ folder missing — running first-time setup")
    if not (ROOT / "capacitor.config.ts").exists():
        (ROOT / "capacitor.config.ts").write_text(
            "import type { CapacitorConfig } from '@capacitor/cli';\n\n"
            "const config: CapacitorConfig = {\n"
            "  appId: 'com.amaha.quranquest',\n"
            "  appName: 'Quran Quest',\n"
            "  webDir: 'dist',\n"
            "  android: { allowMixedContent: true },\n"
            "};\n\n"
            "export default config;\n",
            encoding="utf-8",
        )
    run("npx cap add android")

run("npx cap sync android")


# ── 3. Build the APK ─────────────────────────────────
print("\n" + "═" * 55)
print("  3/5  Build APK (gradle)")
print("═" * 55)

gradlew = "gradlew.bat" if sys.platform.startswith("win") else "./gradlew"
run(f"{gradlew} assembleDebug", cwd=ROOT / "android")

APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
if not APK.exists():
    print(f"X  APK not found at {APK}")
    sys.exit(1)

size_mb = APK.stat().st_size / (1024 * 1024)
print(f"  ✅ APK: {APK.name}  ({size_mb:.1f} MB)")


# ── 4. Install on phone ──────────────────────────────
print("\n" + "═" * 55)
print("  4/5  Install on phone")
print("═" * 55)

r = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if l and "List" not in l]

if not lines:
    print("  ⚠  No phone detected by adb.")
    print(f"     APK at: {APK}")
    print(f"     Manual install:  adb install -r \"{APK}\"")
else:
    print(f"  Device: {lines}")
    run(f'adb install -r "{APK}"', check=False)


# ── 5. Summary ───────────────────────────────────────
print("\n" + "═" * 55)
print("  ✅ Done.")
print("═" * 55)
print(f"""
APK: {APK}
Size: {size_mb:.1f} MB

Open "Quran Quest" on your phone.
""")