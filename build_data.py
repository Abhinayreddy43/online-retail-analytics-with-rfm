"""Pre-compute the dashboard datasets (run once; the app also does this automatically if files are missing)."""
from core import build_and_save, DATA_DIR

if __name__ == "__main__":
    build_and_save()
    print("Saved:", *[p.name for p in DATA_DIR.glob("*.parquet")])
