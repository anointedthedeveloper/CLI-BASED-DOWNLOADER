"""Check what fields the release API returns per episode."""
import subprocess, json

# One Piece series ID as a known example
r = subprocess.run([
    'curl', '-s', '--max-time', '15', '-L',
    '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    '-H', 'Accept: application/json',
    'https://animepahe.com/api?m=release&id=3e25edc6-3387-91e2-c811-faed4f768776&sort=episode_asc&page=1'
], capture_output=True)

try:
    data = json.loads(r.stdout)
    eps = data.get('data', [])
    if eps:
        print("Episode fields:", list(eps[0].keys()))
        print("\nFirst episode:")
        print(json.dumps(eps[0], indent=2))
    else:
        print("No data. Status likely 403.")
        print("Raw:", r.stdout[:300])
except Exception as e:
    print(f"Parse error: {e}")
    print("Raw:", r.stdout[:300])
