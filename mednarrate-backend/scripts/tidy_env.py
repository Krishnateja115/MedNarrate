"""Tidy mednarrate-backend/.env in place without touching any secret.

  * removes duplicate settings (the last value in the file is the one that counts)
  * sets the AI provider order, the Groq/Qwen/OpenRouter models and the admin origin
  * switches off the paid OpenAI and the rate-limited Mistral keys (kept in the file, commented out)
  * writes a backup next to the file first and never prints a value, only setting names

Run from the mednarrate-backend folder:
    python scripts/tidy_env.py --dry-run     # show what would change
    python scripts/tidy_env.py               # do it
"""
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"

SET = {
    "ADMIN_APP_ORIGIN": "http://localhost:3001",
    "LLM_PROVIDER_CHAIN": "groq,groq_qwen,openrouter",
    "TRANSLATION_PROVIDER_ORDER": "gemini,groq_qwen,groq,openrouter",
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_QWEN_MODEL": "qwen/qwen3.8-27b",
    "OPENROUTER_MODEL": "openrouter/free",
}
DISABLE = ["OPENAI_API_KEY", "MISTRAL_API_KEY"]
NEEDED_SECRETS = ["JWT_SECRET", "GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"]
LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")


def main(dry_run: bool) -> None:
    if not ENV.is_file():
        sys.exit(f"No .env found at {ENV}")
    lines = ENV.read_text(encoding="utf-8").splitlines()
    changes = []

    last = {}
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if m:
            last[m.group(1)] = i

    out = []
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if not m:
            out.append(line)
            continue
        name, value = m.group(1), m.group(2)
        if last[name] != i:
            changes.append(f"removed an earlier duplicate of {name}")
            continue
        if name in DISABLE and value.strip():
            out.append(f"# disabled by tidy_env.py (paid or rate limited): {name}={value}")
            changes.append(f"disabled {name} (value kept as a comment)")
            continue
        if name in SET and value.strip() != SET[name]:
            out.append(f"{name}={SET[name]}")
            changes.append(f"set {name}")
            SET_DONE.add(name)
            continue
        if name in SET:
            SET_DONE.add(name)
        out.append(line)

    missing = [k for k in SET if k not in SET_DONE]
    if missing:
        out += ["", "# --- added by tidy_env.py ---"] + [f"{k}={SET[k]}" for k in missing]
        changes += [f"added {k}" for k in missing]

    present = {m.group(1): m.group(2).strip() for l in out if (m := LINE.match(l))}
    empty = [k for k in NEEDED_SECRETS if not present.get(k)]

    print("Changes:" if changes else "Nothing to change.")
    for c in changes:
        print("  -", c)
    if empty:
        print("\nStill empty (fill these in .env yourself):", ", ".join(empty))
    else:
        print("\nAll four secrets are filled in:", ", ".join(NEEDED_SECRETS))

    if dry_run or not changes:
        print("\n(dry run, nothing written)" if dry_run else "")
        return
    backup = ENV.with_name(f".env.backup-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(ENV, backup)
    ENV.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
    print(f"\nWritten. Backup saved as {backup.name}")


SET_DONE: set = set()

if __name__ == "__main__":
    main("--dry-run" in sys.argv)
