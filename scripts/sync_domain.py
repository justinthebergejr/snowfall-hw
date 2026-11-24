"""Copy the report into the existing justi.zone website without changing its homepage."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "index.html", "style.css", "report.js",
    "assets/results.json", "assets/station-years.csv", "assets/manifest.json",
)


def sync(checkout):
    checkout = checkout.resolve()
    if not (checkout / ".git").exists():
        raise SystemExit("Expected a Git checkout of the existing website.")
    if (checkout / "CNAME").read_text().strip() != "justi.zone":
        raise SystemExit("The website CNAME must already be justi.zone.")
    remote = subprocess.check_output(
        ["git", "-C", str(checkout), "remote", "get-url", "origin"], text=True).strip()
    if remote.removesuffix(".git").rstrip("/").split("/")[-1] != "justinsuf.github.io":
        raise SystemExit("Expected the justinsuf.github.io website repository.")
    destination = checkout / "snowfall"
    for name in FILES:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs" / name, target)
    print(f"Copied {len(FILES)} publication files to {destination}")
    print("Review, commit, and push the website checkout to deploy.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("website_checkout", type=Path)
    sync(parser.parse_args().website_checkout)
