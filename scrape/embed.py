"""
Compute sentence embeddings for all papers and save as a binary Float32 file.

Usage:
    cd scrape && uv run embed.py

Requires papers.json to already exist (run scrape.py first).
Model: all-MiniLM-L6-v2 (384 dims, ~90 MB download, cached after first run).
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["sentence-transformers>=3.0", "numpy>=1.26"]
# ///

import json
import struct
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent.parent / "docs" / "data"
PAPERS_PATH = DATA_DIR / "papers.json"
EMB_PATH = DATA_DIR / "embeddings.bin"
META_PATH = DATA_DIR / "embeddings_meta.json"
MODEL_NAME = "all-MiniLM-L6-v2"


def main() -> None:
    if not PAPERS_PATH.exists():
        print(f"ERROR: {PAPERS_PATH} not found. Run scrape.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    papers = data["papers"]
    print(f"Loaded {len(papers)} papers")

    # Encode title + abstract together for richer semantic signal
    texts = [
        f"{p['title']}. {p['abstract']}" if p.get("abstract") else p["title"]
        for p in papers
    ]

    print(f"Loading model {MODEL_NAME}…")
    model = SentenceTransformer(MODEL_NAME)

    print("Computing embeddings…")
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,  # pre-normalize → dot product = cosine similarity
    )

    emb_f32 = embeddings.astype(np.float32)
    emb_f32.tofile(EMB_PATH)

    META_PATH.write_text(
        json.dumps(
            {
                "model": MODEL_NAME,
                "n_papers": len(papers),
                "dim": emb_f32.shape[1],
                "size_mb": round(emb_f32.nbytes / 1024 / 1024, 2),
            },
            indent=2,
        )
    )

    print(f"\nSaved embeddings → {EMB_PATH}")
    print(f"Shape : {emb_f32.shape}  ({emb_f32.nbytes / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
