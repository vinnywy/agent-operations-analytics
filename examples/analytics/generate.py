"""Generate deterministic, non-sensitive data for the public SCAN demonstration."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("sales.csv"))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    start = date(2025, 1, 1)
    rows = []
    for number in range(240):
        day = start + timedelta(days=number)
        channel = ("direct", "partner", "self_service")[number % 3]
        region = ("north", "south")[number % 2]
        cancelled = 1 if rng.random() < (0.10 if channel == "partner" else 0.05) else 0
        revenue = 0 if cancelled else round(rng.uniform(80, 220), 2)
        if number == 170:
            revenue = 2500.00
        rows.append({"order_id": f"S-{number:04d}", "order_date": day.isoformat(), "channel": channel,
                     "region": region, "cancelled": cancelled, "revenue": revenue})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
