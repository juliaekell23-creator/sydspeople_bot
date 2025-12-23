import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _parse_admin_ids(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]

@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]
    base_url: str
    webhook_path: str
    price_csv_url: str | None
    site_base_url: str

    @property
    def webhook_url(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.webhook_path}"

def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is missing")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is missing")

    base_url = os.getenv("BASE_URL", "").strip()
    if not base_url:
        raise RuntimeError("BASE_URL is missing (needed for webhook)")

    webhook_path = os.getenv("WEBHOOK_PATH", "/tg/webhook").strip()

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        base_url=base_url,
        webhook_path=webhook_path,
        price_csv_url=os.getenv("PRICE_CSV_URL"),
        site_base_url=os.getenv("SITE_BASE_URL", "https://example.com").strip(),
    )
