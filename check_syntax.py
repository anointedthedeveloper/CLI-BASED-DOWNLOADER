import ast, os
base = os.path.dirname(os.path.abspath(__file__))
files = ['app.py','animepahe.py','session.py','flaresolverr.py']
for f in files:
    ast.parse(open(os.path.join(base, f), encoding='utf-8').read())
    print(f'OK  {f}')
