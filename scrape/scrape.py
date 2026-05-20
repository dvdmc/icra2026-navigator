"""
Scrape ICRA 2026 program from papercept and save as docs/data/papers.json.

Usage:
    cd scrape && uv run scrape.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.31", "beautifulsoup4>=4.12", "lxml>=5.0"]
# ///

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ras.papercept.net/conferences/conferences/ICRA26/program/"
PAGES = [
    ("ICRA26_ContentListWeb_1.html", "Sunday"),
    ("ICRA26_ContentListWeb_2.html", "Monday"),
    ("ICRA26_ContentListWeb_3.html", "Tuesday"),
    ("ICRA26_ContentListWeb_4.html", "Wednesday"),
    ("ICRA26_ContentListWeb_5.html", "Thursday"),
    ("ICRA26_ContentListWeb_6.html", "Friday"),
]

DAY_ORDER = {d: i for i, (_, d) in enumerate(PAGES)}


def parse_page(html: str, day: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    papers: list[dict] = []

    current_session: dict | None = None
    current_paper: dict | None = None
    collecting_authors = False

    for row in soup.find_all("tr"):
        classes = row.get("class", [])

        # ── Session header row ──────────────────────────────────────────────
        if "sHdr" in classes:
            b_tag = row.find("b")
            anchor = row.find("a", attrs={"name": True})

            if b_tag and anchor:
                # First sHdr of a new session: "<b>TuI1I</b> Interactive Session, Hall C"
                if current_paper:
                    papers.append(current_paper)
                    current_paper = None
                collecting_authors = False

                session_id = b_tag.get_text(strip=True)
                td = row.find("td")
                td_text = td.get_text(separator=" ", strip=True)
                info_text = td_text[len(session_id):].strip()

                # Split room off last comma: "Interactive Session, Hall C"
                if "," in info_text:
                    session_type, room = info_text.rsplit(",", 1)
                    session_type = session_type.strip()
                    room = room.strip()
                else:
                    session_type = info_text
                    room = ""

                current_session = {
                    "id": session_id,
                    "type": session_type,
                    "room": room,
                    "day": day,
                    "title": "",
                }

            elif current_session:
                # Subsequent sHdr rows carry the human-readable session title
                a_tag = row.find("a", href=True)
                if a_tag:
                    current_session["title"] = a_tag.get_text(strip=True)

        # ── Paper header row ────────────────────────────────────────────────
        elif "pHdr" in classes:
            if current_paper:
                papers.append(current_paper)

            anchor = row.find("a", attrs={"name": True})
            if anchor and current_session:
                text = anchor.get_text(strip=True)
                # "09:00-10:30, Paper TuI1I.1"
                m = re.match(r"(\d+:\d+-\d+:\d+),\s*Paper\s+(.+)", text)
                time_slot = m.group(1) if m else ""
                paper_id = m.group(2) if m else text

                current_paper = {
                    "id": paper_id,
                    "time": time_slot,
                    "session_id": current_session["id"],
                    "session_type": current_session["type"],
                    "session_title": current_session["title"],
                    "day": day,
                    "room": current_session["room"],
                    "title": "",
                    "authors": [],
                    "keywords": [],
                    "abstract": "",
                }
                collecting_authors = False

        # ── Paper content rows ───────────────────────────────────────────────
        elif current_paper is not None:
            # Title
            ptitl = row.find("span", class_="pTtl")
            if ptitl:
                current_paper["title"] = ptitl.get_text(strip=True)
                collecting_authors = True
                continue

            # Abstract/keywords div  (id="Ab<N>")
            ab_div = row.find("div", id=re.compile(r"^Ab\d+$"))
            if ab_div:
                collecting_authors = False
                kw_links = ab_div.find_all(
                    "a", href=lambda h: h and "KeywordIndex" in h
                )
                current_paper["keywords"] = [a.get_text(strip=True) for a in kw_links]

                raw = ab_div.get_text(separator=" ")
                if "Abstract:" in raw:
                    abstract = raw.split("Abstract:", 1)[1].strip()
                    current_paper["abstract"] = re.sub(r"\s+", " ", abstract)
                continue

            # Author rows (two-cell rows with an AuthorIndex link)
            if collecting_authors:
                tds = row.find_all("td", recursive=False)
                if len(tds) == 2:
                    author_link = tds[0].find(
                        "a", href=lambda h: h and "AuthorIndex" in h
                    )
                    if author_link:
                        current_paper["authors"].append(
                            {
                                "name": author_link.get_text(strip=True),
                                "affiliation": tds[1].get_text(strip=True),
                            }
                        )

    if current_paper:
        papers.append(current_paper)

    return papers


def main() -> None:
    all_papers: list[dict] = []
    all_keywords: set[str] = set()
    all_session_types: set[str] = set()

    session = requests.Session()
    session.headers["User-Agent"] = "ICRA26-digest-scraper/1.0"

    for filename, day in PAGES:
        url = BASE_URL + filename
        print(f"Fetching {day} … {url}")
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue

        papers = parse_page(resp.text, day)
        print(f"  → {len(papers)} papers")
        all_papers.extend(papers)

        for p in papers:
            all_keywords.update(p["keywords"])
            if p["session_type"]:
                all_session_types.add(p["session_type"])

    out = {
        "papers": all_papers,
        "keywords": sorted(all_keywords, key=str.casefold),
        "sessionTypes": sorted(all_session_types, key=str.casefold),
        "days": [d for _, d in PAGES],
        "total": len(all_papers),
        "conference": {
            "name": "IEEE International Conference on Robotics & Automation",
            "short": "ICRA 2026",
            "location": "Vienna, Austria",
            "dates": "June 1–5, 2026",
        },
    }

    out_path = Path(__file__).parent.parent / "docs" / "data" / "papers.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSaved {len(all_papers)} papers → {out_path}")
    print(f"Unique keywords : {len(all_keywords)}")
    print(f"Session types   : {sorted(all_session_types)}")


if __name__ == "__main__":
    main()
