import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    import animepahe
except ImportError:
    raise SystemExit("Cannot import animepahe.py. Ensure this script is run from the Animedownloader folder and the parent repository is available.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <query>")
        raise SystemExit(1)

    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("Query cannot be empty.")
        raise SystemExit(1)

    results = animepahe.search_anime(query, log=lambda msg: None, use_flaresolverr=False)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
