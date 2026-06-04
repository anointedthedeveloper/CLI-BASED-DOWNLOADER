"""Delete wrong-version ChromeDriver so uc downloads the correct one."""
import os, glob, shutil

# Common uc cache locations
locations = [
    os.path.expanduser("~\\appdata\\roaming\\undetected_chromedriver"),
    os.path.expanduser("~\\appdata\\local\\undetected_chromedriver"),
    os.path.join(os.environ.get("TEMP",""), "undetected_chromedriver"),
    os.path.join(os.environ.get("LOCALAPPDATA",""), "undetected_chromedriver"),
]

import undetected_chromedriver as uc
# Also check where uc stores the driver
try:
    import appdirs
    locations.append(appdirs.user_data_dir("undetected_chromedriver"))
except ImportError:
    pass

found = []
for loc in locations:
    if os.path.exists(loc):
        found.append(loc)
        print(f"Found: {loc}")
        for f in glob.glob(os.path.join(loc, "**", "chromedriver*"), recursive=True):
            print(f"  Removing: {f}")
            try:
                os.remove(f)
            except Exception as e:
                print(f"  Could not remove: {e}")

# Also check the module's own directory
uc_dir = os.path.dirname(uc.__file__)
for f in glob.glob(os.path.join(uc_dir, "**", "chromedriver*"), recursive=True):
    print(f"Found in uc dir: {f}")
    found.append(f)
    try:
        os.remove(f)
        print(f"  Removed")
    except Exception as e:
        print(f"  Could not remove: {e}")

if not found:
    print("No cached ChromeDriver found - checking Program Files...")
    
    # The driver might be stored by selenium manager
    selenium_dir = os.path.join(os.environ.get("LOCALAPPDATA",""), 
                                "selenium-manager", "chrome")
    if os.path.exists(selenium_dir):
        print(f"Selenium manager cache: {selenium_dir}")
        for f in glob.glob(os.path.join(selenium_dir, "**"), recursive=True):
            if "chromedriver" in f.lower():
                print(f"  {f}")

print("\nDone. Re-run test_uc.py to let uc download the correct ChromeDriver 148.")
