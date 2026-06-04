"""Check which endpoints actually respond without CF challenge."""
import subprocess, json

def curl(url):
    r = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', '--max-time', '15',
         '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
         '-H', 'Accept: application/json, text/javascript, */*',
         '-H', 'Referer: https://animepahe.com/',
         url],
        capture_output=True
    )
    out = r.stdout.decode('utf-8', errors='replace')
    lines = out.rsplit('\n', 1)
    body = lines[0][:200] if len(lines) > 1 else ''
    code = lines[-1].strip() if len(lines) > 1 else '?'
    return code, body

tests = [
    ("animepahe.com API search",   "https://animepahe.com/api?m=search&q=one+piece"),
    ("animepahe.com API release",  "https://animepahe.com/api?m=release&id=3e25edc6-3387-91e2-c811-faed4f768776&sort=episode_asc&page=1"),
    ("animepahe.com page",         "https://animepahe.com/anime/3e25edc6-3387-91e2-c811-faed4f768776"),
    ("animepahe.pw page",          "https://animepahe.pw/anime/3e25edc6-3387-91e2-c811-faed4f768776"),
]

for label, url in tests:
    code, body = curl(url)
    is_json = body.strip().startswith('{') or body.strip().startswith('[')
    is_cf   = 'cloudflare' in body.lower() or 'just a moment' in body.lower()
    status = '✓ JSON' if is_json else ('✗ CF block' if is_cf else f'? html')
    print(f"  {code}  {status:<12}  {label}")
    if is_json:
        print(f"         preview: {body[:120]}")
