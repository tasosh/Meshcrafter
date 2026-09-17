#!/usr/bin/env python3
"""One-command deploy of this folder to a Hugging Face Space.

Usage:
    export HF_TOKEN=hf_...          # a WRITE token from hf.co/settings/tokens
    python deploy.py <username-or-org>/Meshcrafter

Requires: pip install huggingface_hub
"""
import os
import sys

from huggingface_hub import HfApi

FILES = ["app.py", "requirements.txt", "README.md"]


def main():
    if len(sys.argv) != 2 or "/" not in sys.argv[1]:
        print(__doc__)
        sys.exit(1)
    repo_id = sys.argv[1]

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Set HF_TOKEN to a write token first (hf.co/settings/tokens).")
        sys.exit(1)

    here = os.path.dirname(os.path.abspath(__file__))
    missing = [f for f in FILES if not os.path.exists(os.path.join(here, f))]
    if missing:
        print(f"Missing files next to deploy.py: {missing}")
        sys.exit(1)

    api = HfApi(token=token)
    print(f"Creating Space {repo_id} (no-op if it already exists)...")
    api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="gradio", exist_ok=True)

    for f in FILES:
        print(f"Uploading {f}...")
        api.upload_file(
            path_or_fileobj=os.path.join(here, f),
            path_in_repo=f,
            repo_id=repo_id,
            repo_type="space",
        )

    print()
    print(f"Done. The Space is building now at: https://huggingface.co/spaces/{repo_id}")
    print("First build takes a couple of minutes; watch the Logs tab if it doesn't come up.")


if __name__ == "__main__":
    main()
