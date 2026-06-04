import subprocess, time, requests as req, sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

print("Launching Chrome with remote debugging...")
proc = subprocess.Popen([
    CHROME,
    "--remote-debugging-port=9222",
    "--no-first-run",
    "--no-default-browser-check",
    "https://animepahe.com/"
])

time.sleep(4)

try:
    r = req.get("http://localhost:9222/json/version", timeout=5)
    print("CDP response:", r.status_code)
    print("Browser:", r.json().get("Browser", "?"))
    print("OK - CDP works!")
except Exception as e:
    print("CDP error:", e)

# now try playwright connecting to it
try:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    print("Playwright connected!")
    print("Title:", page.title())
    print("URL:", page.url)
    cookies = ctx.cookies()
    print("Cookies:", [(c["name"], c["domain"]) for c in cookies if "animepahe" in c.get("domain","") or "cloudflare" in c.get("name","").lower()])
    browser.close()
    pw.stop()
except Exception as e:
    print("Playwright CDP error:", e)

proc.terminate()
print("done")
