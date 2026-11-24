"""Push main and enable GitHub Pages from docs/ using Git's credential manager.

Requires repository administration permission. Credentials are never printed or saved.
"""
import json
import subprocess
import urllib.error
import urllib.request

REPOSITORY = "justinthebergejr/snowfall-hw"


def main():
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("Commit your reviewed changes before publishing.")
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    result = subprocess.run(
        ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
        text=True, capture_output=True, check=True)
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = credential.get("password")
    if not token:
        raise SystemExit("No GitHub credential found. Enable Pages manually: main /docs.")
    def request(method, path, body=None):
        req = urllib.request.Request(
            "https://api.github.com/repos/" + REPOSITORY + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    try:
        request("GET", "/pages")
        request("PUT", "/pages", {"source": {"branch": "main", "path": "/docs"},
                                  "build_type": "legacy"})
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise SystemExit(f"Pages API returned HTTP {error.code}; enable Pages in repository settings.")
        try:
            request("POST", "/pages", {"source": {"branch": "main", "path": "/docs"},
                                       "build_type": "legacy"})
        except urllib.error.HTTPError as failure:
            raise SystemExit(f"Pages creation returned HTTP {failure.code}; enable Pages in repository settings.")
    print("GitHub Pages configured: https://justinthebergejr.github.io/snowfall-hw/")
    print("The initial deployment may take a few minutes.")


if __name__ == "__main__":
    main()
