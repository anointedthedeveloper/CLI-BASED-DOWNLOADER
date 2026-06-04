import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    import flaresolverr
except ImportError:
    raise SystemExit("Cannot import flaresolverr.py. Ensure this script is run from the Animedownloader folder and the parent repository is available.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python flaresolverr_wrapper.py <status|start|stop>")
        raise SystemExit(1)

    command = sys.argv[1].lower()
    if command == "status":
        print("running" if flaresolverr.is_running() else "stopped")
    elif command == "start":
        success = flaresolverr.start_bundled()
        print("started" if success else "failed")
    elif command == "stop":
        flaresolverr.stop_bundled()
        print("stopped")
    else:
        print("Usage: python flaresolverr_wrapper.py <status|start|stop>")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
