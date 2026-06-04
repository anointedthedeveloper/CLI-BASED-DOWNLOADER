import os
import time
import subprocess
import argparse

def get_git_status():
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def push_changes():
    print("Changes detected. Committing and pushing...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update: sync downloaded episodes & changes"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Push successful.")
    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto-push changes in a git repository.")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds (default: 10)")
    args = parser.parse_args()

    # Ensure we're in a git repository
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Current directory is not a git repository.")
        return

    print(f"Starting autopush. Checking for changes every {args.interval} seconds.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            status = get_git_status()
            if status:
                push_changes()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping autopush.")

if __name__ == "__main__":
    main()
