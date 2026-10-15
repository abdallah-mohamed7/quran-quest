"""One-shot patch: adds touch control support to LevelScene.ts.
Creates a .bak backup first. Idempotent-ish: safe to run twice."""
import pathlib
import re
import shutil
import sys

FILE = pathlib.Path("src/game/scenes/LevelScene.ts")

if not FILE.exists():
    print(f"❌ Not found: {FILE}")
    print("   Run this from the quran-quest folder.")
    sys.exit(1)

src = FILE.read_text(encoding="utf-8")
original = src

# ── Backup ────────────────────────────────────────────
backup = FILE.with_suffix(".ts.bak")
if not backup.exists():
    shutil.copy2(FILE, backup)
    print(f"💾 Backup saved: {backup}")

changes = 0


# ══════════════════════════════════════════════════════
# 1. Add virtual input fields
# ══════════════════════════════════════════════════════
anchor_fields = "  private landedThisFrame = false;"
new_fields = (
    "  private landedThisFrame = false;\n"
    "  private virtualLeft = false;\n"
    "  private virtualRight = false;\n"
    "  private virtualJump = false;"
)

if "virtualLeft" in src:
    print("⏭  Fields already present, skipping")
elif anchor_fields in src:
    src = src.replace(anchor_fields, new_fields, 1)
    print("✅ Added virtual input fields")
    changes += 1
else:
    print(f"⚠  Could not find anchor for fields: {anchor_fields!r}")
    print("   Make sure LevelScene.ts has that exact line.")


# ══════════════════════════════════════════════════════
# 2. Add bus listeners in create()
# ══════════════════════════════════════════════════════
anchor_listen = "    this.keys.jump.on('down', () => { this.jumpQueuedAt = this.time.now; });"
listeners = anchor_listen + """

    // ── Touch input from the UI ──────────────────────
    bus.on('input:left:down',  () => { this.virtualLeft  = true;  });
    bus.on('input:left:up',    () => { this.virtualLeft  = false; });
    bus.on('input:right:down', () => { this.virtualRight = true;  });
    bus.on('input:right:up',   () => { this.virtualRight = false; });
    bus.on('input:jump:down',  () => {
      this.virtualJump = true;
      this.jumpQueuedAt = this.time.now;
    });
    bus.on('input:jump:up',    () => { this.virtualJump = false; });

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      bus.off('input:left:down');
      bus.off('input:left:up');
      bus.off('input:right:down');
      bus.off('input:right:up');
      bus.off('input:jump:down');
      bus.off('input:jump:up');
    });"""

if "input:left:down" in src:
    print("⏭  Bus listeners already present, skipping")
elif anchor_listen in src:
    src = src.replace(anchor_listen, listeners, 1)
    print("✅ Added bus listeners in create()")
    changes += 1
else:
    print("⚠  Could not find anchor for bus listeners")
    print(f"   Expected: {anchor_listen!r}")


# ══════════════════════════════════════════════════════
# 3. Combine keyboard + touch in update()
# ══════════════════════════════════════════════════════

# 3a — horizontal input
anchor_h = (
    "    const wantLeft  = this.keys.left.isDown;\n"
    "    const wantRight = this.keys.right.isDown;"
)
replace_h = (
    "    const wantLeft  = this.keys.left.isDown  || this.virtualLeft;\n"
    "    const wantRight = this.keys.right.isDown || this.virtualRight;"
)
if "this.keys.left.isDown  || this.virtualLeft" in src:
    print("⏭  Horizontal input already combined, skipping")
elif anchor_h in src:
    src = src.replace(anchor_h, replace_h, 1)
    print("✅ Combined horizontal input (keyboard + touch)")
    changes += 1
else:
    print("⚠  Could not find horizontal input anchor")

# 3b — jump hold (isDown check)
anchor_jump1 = "    if (this.jumpHeld && this.keys.jump.isDown && isJumping) {"
replace_jump1 = "    if (this.jumpHeld && (this.keys.jump.isDown || this.virtualJump) && isJumping) {"
if "(this.keys.jump.isDown || this.virtualJump)" in src:
    print("⏭  Jump-hold already combined, skipping")
elif anchor_jump1 in src:
    src = src.replace(anchor_jump1, replace_jump1, 1)
    print("✅ Combined jump-hold check")
    changes += 1
else:
    print("⚠  Could not find jump-hold anchor")

# 3c — jump release (also cancel on touch release)
anchor_jump2 = "    if (this.jumpHeld && !this.keys.jump.isDown && isJumping) {"
replace_jump2 = "    if (this.jumpHeld && !this.keys.jump.isDown && !this.virtualJump && isJumping) {"
if "!this.keys.jump.isDown && !this.virtualJump" in src:
    print("⏭  Jump-release already combined, skipping")
elif anchor_jump2 in src:
    src = src.replace(anchor_jump2, replace_jump2, 1)
    print("✅ Combined jump-release check")
    changes += 1
else:
    print("⚠  Could not find jump-release anchor")


# ── Write back ────────────────────────────────────────
if src != original:
    FILE.write_text(src, encoding="utf-8")
    print(f"\n✅ Wrote {changes} changes to {FILE}")
    print(f"   Backup at: {backup}")
else:
    print("\n⏭  No changes made (file already patched, or anchors not found)")

print("\nDone. Reload the browser to test.")