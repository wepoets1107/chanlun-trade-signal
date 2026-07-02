"""Push all files via Contents API (works on fresh empty repos)."""
import subprocess, json, os, base64, urllib.request, urllib.error

REPO = "wepoets1107/chanlun-trade-signal"
ROOT = r"C:\Users\张无忌\Desktop\workbuddy\chanlun-risk-mcp"
IGNORE_DIRS = {".git", "__pycache__"}

def gh_auth_token():
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

files = []
for dirpath, dirs, filenames in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for fn in filenames:
        fpath = os.path.join(dirpath, fn)
        rel = os.path.relpath(fpath, ROOT).replace(os.sep, "/")
        with open(fpath, "rb") as f:
            content = f.read()
        files.append((rel, base64.b64encode(content).decode()))

token = gh_auth_token()
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
}

# Create first file to bootstrap the repo
print("Pushing files via Contents API...")
file_count = 0
for path, content in files:
    api_path = path.replace("\\", "/")
    url = f"https://api.github.com/repos/{REPO}/contents/{api_path}"
    payload = {
        "message": f"add {path}",
        "content": content,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            file_count += 1
            result = json.loads(resp.read())
            print(f"  [{file_count:2d}] {path}")
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  FAILED [{e.code}] {path}: {err[:100]}")

print(f"\nDone: {file_count}/{len(files)} files pushed")
print(f"https://github.com/{REPO}")
