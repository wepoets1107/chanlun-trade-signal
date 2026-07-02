"""Initialize empty repo with a README, then push all files."""
import subprocess, json, os, base64, urllib.request, urllib.error

REPO = "wepoets1107/chanlun-trade-signal"
ROOT = r"C:\Users\张无忌\Desktop\workbuddy\chanlun-risk-mcp"
IGNORE_DIRS = {".git", "__pycache__"}

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
        raise

# Step 1: Create README.md as initial file (Contents API works on empty repos)
print("Creating initial README.md...")
with open(os.path.join(ROOT, "README.md"), "rb") as f:
    readme_content = base64.b64encode(f.read()).decode()

init = gh_api("PUT", f"repos/{REPO}/contents/README.md", {
    "message": "init: ChanLun trade signal workbench",
    "content": readme_content,
})
if not init:
    print("Failed to create initial file!")
    exit(1)

print(f"README created, commit: {init['commit']['sha'][:7]}")

# Step 2: Now the repo has a commit, collect all files and push via tree
files = []
for dirpath, dirs, filenames in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for fn in filenames:
        fpath = os.path.join(dirpath, fn)
        rel = os.path.relpath(fpath, ROOT).replace(os.sep, "/")
        if rel == "README.md":
            continue  # already created
        with open(fpath, "rb") as f:
            content = f.read()
        try:
            text = content.decode("utf-8")
            files.append({"path": rel, "content": text})
        except UnicodeDecodeError:
            b64 = base64.b64encode(content).decode()
            files.append({"path": rel, "content": b64, "encoding": "base64"})

print(f"\nCreating {len(files)} blobs...")
tree_items = []
for f in files:
    blob = gh_api("POST", f"repos/{REPO}/git/blobs", {
        "content": f["content"],
        "encoding": f.get("encoding", "utf-8"),
    })
    if not blob:
        print(f"  FAILED: {f['path']}")
        continue
    tree_items.append({
        "path": f["path"],
        "mode": "100644",
        "type": "blob",
        "sha": blob["sha"],
    })
    print(f"  {f['path']}")

print("\nCreating tree (base tree: " + init["content"]["sha"] + ")...")
# Get the base tree from README
readme_sha = init["content"]["sha"]
tree = gh_api("POST", f"repos/{REPO}/git/trees", {
    "base_tree": init["commit"]["sha"],  # use commit as base
    "tree": tree_items,
})
if not tree:
    print("Failed to create tree!")
    exit(1)

print("Creating commit...")
commit = gh_api("POST", f"repos/{REPO}/git/commits", {
    "message": "add: all project files",
    "tree": tree["sha"],
    "parents": [init["commit"]["sha"]],
})
if not commit:
    print("Failed to create commit!")
    exit(1)

print("Updating ref...")
ref = gh_api("PATCH", f"repos/{REPO}/git/refs/heads/main", {
    "sha": commit["sha"],
    "force": True,
})
if ref:
    print(f"\nDone! https://github.com/{REPO}")
else:
    print("Failed to update ref")
