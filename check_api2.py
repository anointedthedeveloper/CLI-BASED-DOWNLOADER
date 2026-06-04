"""Follow redirects and check final destination + cookies needed."""
import subprocess

def curl_follow(url):
    r = subprocess.run(
        ['curl', '-s', '-L', '--max-redirs', '5',
         '-w', '\n---HTTPCODE:%{http_code}\n---FINALURL:%{url_effective}',
         '--max-time', '20',
         '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
         '-H', 'Accept: application/json, text/javascript, */*',
         '-H', 'Referer: https://animepahe.com/',
         url],
        capture_output=True
    )
    out  = r.stdout.decode('utf-8', errors='replace')
    body = out[:300]
    code = ''
    final = ''
    for line in out.split('\n'):
        if line.startswith('---HTTPCODE:'): code  = line.split(':',1)[1]
        if line.startswith('---FINALURL:'): final = line.split(':',1)[1]
    is_json = '{' in body[:50] or '[' in body[:50]
    is_cf   = 'cloudflare' in body.lower() or 'just a moment' in body.lower() or 'challenge' in body.lower()
    tag = '✓ JSON data' if is_json else ('✗ CF challenge' if is_cf else '? other')
    print(f"\n[{code}] {tag}")
    print(f"  orig:  {url}")
    if final.strip() != url: print(f"  final: {final.strip()}")
    if is_json: print(f"  data:  {body[:200]}")

curl_follow("https://animepahe.com/api?m=search&q=one+piece")
curl_follow("https://animepahe.com/api?m=release&id=3e25edc6-3387-91e2-c811-faed4f768776&sort=episode_asc&page=1")
curl_follow("https://animepahe.pw/play/3e25edc6-3387-91e2-c811-faed4f768776/ed28bf01e38ff3a91af31af60a1a929e15f43cc9b26df4ed487dd0e84b3dc0be")
