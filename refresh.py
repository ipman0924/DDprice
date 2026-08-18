"""Download the Dicker Data CSV feed, validate it, and write data/feed.parquet + data/meta.json.

Runs in GitHub Actions daily and can also be run locally to seed the data folder.

Reads the download URL from the DD_DOWNLOAD_URL environment variable.
"""
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

EXPECTED_HEADER = [
    "StockCode", "Vendor", "VendorStockCode", "StockDescription",
    "PrimaryCategory", "SecondaryCategory", "TertiaryCategory",
    "RRPEx", "DealerEx", "StockAvailable", "ETA", "Status", "Type",
    "BundledItem1", "BundledItem2", "BundledItem3", "BundledItem4", "BundledItem5",
]
MIN_ROWS = 50_000
MAX_ATTEMPTS = 3
RETRY_SPACING_SECONDS = 300

DATA_DIR = Path("data")
TMP_CSV = Path("tmp_feed.csv")


def download(url: str, target: Path) -> None:
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            body = resp.content
            if b"API calls quota exceeded" in body[:512]:
                raise RuntimeError(f"rate-limited by DD portal: {body[:200]!r}")
            if len(body) < 1024:
                raise RuntimeError(f"suspiciously small body ({len(body)} bytes): {body[:200]!r}")
            target.write_bytes(body)
            print(f"downloaded {len(body):,} bytes on attempt {attempt}")
            return
        except Exception as e:
            last_err = e
            print(f"attempt {attempt}/{MAX_ATTEMPTS} failed: {e}", file=sys.stderr)
            if attempt < MAX_ATTEMPTS:
                print(f"sleeping {RETRY_SPACING_SECONDS}s before retry", file=sys.stderr)
                time.sleep(RETRY_SPACING_SECONDS)
    raise RuntimeError(f"all {MAX_ATTEMPTS} download attempts failed: {last_err}")


def validate_and_parse(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    if list(df.columns) != EXPECTED_HEADER:
        raise ValueError(
            f"unexpected header. got={list(df.columns)} expected={EXPECTED_HEADER}"
        )
    if len(df) < MIN_ROWS:
        raise ValueError(f"row count {len(df)} below minimum {MIN_ROWS}")
    if (df["StockCode"] == "").any():
        blanks = int((df["StockCode"] == "").sum())
        raise ValueError(f"{blanks} rows have blank StockCode")

    df["RRPEx"] = pd.to_numeric(df["RRPEx"], errors="raise")
    df["DealerEx"] = pd.to_numeric(df["DealerEx"], errors="raise")
    df["StockAvailable"] = pd.to_numeric(df["StockAvailable"], errors="raise").astype("int64")

    # Drop columns we don't surface in the app. BundledItem1..5 aren't part of the
    # browse workflow (see ADR-0014). Header validation above still checks the full
    # DD-shipped schema, so we notice if DD ever changes upstream.
    drop_cols = [c for c in df.columns if c.startswith("BundledItem")]
    df = df.drop(columns=drop_cols)
    return df


def write_outputs(df: pd.DataFrame, source_bytes: bytes) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DATA_DIR / "feed.parquet", index=False, compression="snappy")
    meta = {
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": int(len(df)),
        "source_bytes": len(source_bytes),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    }
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"wrote data/feed.parquet ({len(df):,} rows) and data/meta.json")


def main() -> int:
    url = os.environ.get("DD_DOWNLOAD_URL", "").strip()
    if not url:
        print("ERROR: DD_DOWNLOAD_URL is not set", file=sys.stderr)
        return 1
    try:
        download(url, TMP_CSV)
        source_bytes = TMP_CSV.read_bytes()
        df = validate_and_parse(TMP_CSV)
        write_outputs(df, source_bytes)
    finally:
        if TMP_CSV.exists():
            TMP_CSV.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
