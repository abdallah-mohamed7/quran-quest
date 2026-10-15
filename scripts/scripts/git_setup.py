"""Prepare the project for GitHub: .gitignore, README, cleanup."""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(".").resolve()
if not (ROOT / "package.json").exists():
    print("❌ run from inside quran-quest")
    sys.exit(1)


# ══════════════════════════════════════════════════════════
# 1. .gitignore
# ══════════════════════════════════════════════════════════
print("═══ 1/4  Writing .gitignore ═══")

GITIGNORE = """# ── Node ─────────────────────────────
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# ── Vite / build output ──────────────
dist/
dist-ssr/
.vite/
*.local

# ── Capacitor / Android ──────────────
android/
ios/
.capacitor/

# ── Quran page audio (huge, ~1.5 GB) ─
# Kept local only. Restore by running:
#   python scripts/import_audio.py
public/quran/audio/pages/*.mp3

# ── Quran page images (keep — small) ─
# (No ignore. ~40 MB total, fine for git.)
# If it grows, uncomment:
# public/quran/pages/*.webp

# ── Backups & logs ───────────────────
_backups/
*.bak
*.bak2
*.bak3
*.bak4
*.bak5
*.bak_*

# ── Editor / OS ──────────────────────
.vscode/*
!.vscode/extensions.json
.idea/
*.swp
.DS_Store
Thumbs.db

# ── Env ──────────────────────────────
.env
.env.local
.env.*.local
"""

GI = ROOT / ".gitignore"
if GI.exists():
    shutil.copy2(GI, GI.with_suffix(".bak"))
GI.write_text(GITIGNORE, encoding="utf-8")
print(f"  ✅ .gitignore written")


# ══════════════════════════════════════════════════════════
# 2. README
# ══════════════════════════════════════════════════════════
print("\n═══ 2/4  Writing README.md ═══")
