import subprocess

print("📦 Installing Playwright Chromium...")
subprocess.run(["playwright", "install", "chromium"], check=True)
