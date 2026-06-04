import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from downloader import download
except ImportError:
    raise SystemExit("Cannot import downloader.py. Ensure this script is run from the Animedownloader folder and the parent repository is available.")


def main():
    if len(sys.argv) < 4:
        print("Usage: python download.py <url> <referer> <dest_dir> [filename]")
        raise SystemExit(1)

    url = sys.argv[1]
    referer = sys.argv[2]
    dest_dir = sys.argv[3]
    filename = sys.argv[4] if len(sys.argv) >= 5 else ""

    print(f"Downloading from: {url}")
    print(f"Destination: {dest_dir}")
    try:
        result = download(url, referer, dest_dir, filename=filename)
        print(f"Saved to: {result}")
    except Exception as exc:
        print(f"Download failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
