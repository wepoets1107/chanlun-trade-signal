"""Push repo to GitHub via REST API (bypasses git HTTPS proxy issues)."""
import subprocess, json, os, base64, urllib.request, urllib.error

REPO = "wepoets1107/chanlun-trade-signal"
ROOT = r"C:\Users\张无忌\Desktop\workbuddy\chanlun-risk-mcp"
IGNORE_DIRS = {".git", "__pycache__", ".git"}

def gh_auth_token():
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

def gh_api(method, endpoint, data=None):
    token = gh_auth_token()
    url = f"https://api.github.com/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  HTTP {e.code}: {err[:200]}")
        return None

def collect_files():
    files = []
    for dirpath, dirs, filenames in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in filenames:
            fpath = os.path.join(dirpath, fn)
            rel = os.path.relpath(fpath, ROOT).replace(os.sep, "/")
            with open(fpath, "rb") as f:
                content = f.read()
            try:
                text = content.decode("utf-8")
                files.append({"path": rel, "content": text})
            except UnicodeDecodeError:
                b64 = base64.b64encode(content).decode()
                files.append({"path": rel, "content": b64, "encoding": "base64"})
    return files

def main():
    print("Collecting files...")
    files = collect_files()
    print(f"Total: {len(files)} files")

    # Create initial commit via Git Data API
    print("Creating blobs...")
    tree_items = []
    for f in files:
        blob = gh_api("POST", f"repos/{REPO}/git/blobs", {
            "content": f["content"],
            "encoding": f.get("encoding", "utf-8"),
        })
        if not blob:
            print(f"  Failed to create blob for {f['path']}")
            continue
        mode = "100644"  # regular file
        tree_items.append({
            "path": f["path"],
            "mode": mode,
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"  {f['path']} -> {blob['sha'][:7]}")

    print("Creating tree...")
    tree = gh_api("POST", f"repos/{REPO}/git/trees", {
        "tree": tree_items,
    })
    if not tree:
        print("Failed to create tree!")
        return

    print("Creating commit...")
    commit = gh_api("POST", f"repos/{REPO}/git/commits", {
        "message": "init: ChanLun trade signal workbench",
        "tree": tree["sha"],
    })
    if not commit:
        print("Failed to create commit!")
        return

    print("Updating ref...")
    ref = gh_api("PATCH", f"repos/{REPO}/git/refs/heads/main", {
        "sha": commit["sha"],
        "force": True,
    })
    if ref:
        print(f"Done! https://github.com/{REPO}")
    else:
        # Try creating the ref
        ref = gh_api("POST", f"repos/{REPO}/git/refs", {
            "ref": "refs/heads/main",
            "sha": commit["sha"],
        })
        if ref:
            print(f"Done! https://github.com/{REPO}")
        else:
            print("Failed to update ref")

if __name__ == "__main__":
    main()
