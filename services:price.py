import aiohttp
import csv
from io import StringIO

async def fetch_price_text(csv_url: str, max_rows: int = 30) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(csv_url, timeout=15) as resp:
            resp.raise_for_status()
            text = await resp.text()

    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if not rows:
        return "Прайс пустой."

    # ожидаем: Название | Цена | Наличие (можно любые колонки — просто покажем первые 3)
    lines = []
    for i, r in enumerate(rows[:max_rows], start=1):
        if not any(cell.strip() for cell in r):
            continue
        a = (r[0].strip() if len(r) > 0 else "")
        b = (r[1].strip() if len(r) > 1 else "")
        c = (r[2].strip() if len(r) > 2 else "")
        line = " — ".join([x for x in [a, b, c] if x])
        lines.append(line)

    return "Актуальный прайс:\n\n" + "\n".join(f"• {x}" for x in lines)
