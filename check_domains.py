import subprocess

domains = ['animepahe.com', 'animepahe.pw', 'animepahe.si', 'animepahe.org', 'animepahe.ru']
for d in domains:
    r = subprocess.run(
        ['curl', '-s', '-o', 'nul', '-w', '%{http_code}', '--max-time', '10', '-L', f'https://{d}'],
        capture_output=True
    )
    print(f'{d}: {r.stdout.decode().strip()}')
