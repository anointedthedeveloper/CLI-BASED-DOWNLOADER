"""Quick test of undetected-chromedriver against animepahe.pw"""
import sys, os
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_solver

print("Testing undetected-chromedriver against animepahe.pw...", flush=True)
print("(tries headless first, then visible window - may take up to 90 seconds)\n", flush=True)

try:
    cookies = cf_solver.solve("https://animepahe.pw", headless=True, timeout=45)
    cf = cookies.get("cf_clearance", "")
    print(f"Cookies received: {list(cookies.keys())}", flush=True)
    if cf:
        print(f"SUCCESS! Got cf_clearance: {cf[:30]}...", flush=True)
        print(f"Total cookies: {len(cookies)}", flush=True)
        print("\nNow testing API with the cookies...", flush=True)
        import session
        resp = session.request("GET", "https://animepahe.pw/api?m=search&q=one+piece")
        print(f"API response: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"Results: {len(data.get('data', []))} anime found", flush=True)
                print("EVERYTHING WORKS!", flush=True)
            except Exception:
                print(f"Got 200 but not JSON. Body: {resp.text[:200]}", flush=True)
        else:
            print(f"API still blocked: {resp.status_code}", flush=True)
            print(f"Body: {resp.text[:200]}", flush=True)
    else:
        print(f"No cf_clearance obtained. CF may require a visible browser window.", flush=True)
        print("The app will open a brief Chrome window to solve the challenge.", flush=True)
except Exception as e:
    print(f"FAILED: {e}", flush=True)
    import traceback; traceback.print_exc()
