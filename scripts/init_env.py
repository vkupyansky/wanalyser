import os
import secrets
from pathlib import Path


def main() -> None:
    target = Path(".env")
    if target.exists():
        raise SystemExit(".env уже существует; файл не изменён")
    template = Path(".env.example").read_text(encoding="utf-8")
    content = template.replace("WEBHOOK_SECRET=\n", f"WEBHOOK_SECRET={secrets.token_urlsafe(32)}\n")
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content)
    print("Создан .env с правами 0600; заполните внешние параметры")


if __name__ == "__main__":
    main()
