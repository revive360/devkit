"""Check every contribution commit in a trusted base..head range for DCO."""
import os
import re
import subprocess


def valid_signoff(message: str, author_name: str, author_email: str) -> bool:
    # Only the final trailer block counts; quoted text elsewhere is not a sign-off.
    blocks = message.strip().split("\n\n")
    if len(blocks) < 2:
        return False
    tail = blocks[-1]
    trailers = re.findall(r"^Signed-off-by: (.+?) <([^<>\s]+@[^<>\s]+)>\s*$", tail, re.MULTILINE | re.IGNORECASE)
    return any(name.strip() == author_name and email.casefold() == author_email.casefold()
               for name, email in trailers)


def check(base: str, head: str) -> int:
    for revision in (base, head):
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("DCO base/head must be full commit SHAs")
    commits = subprocess.check_output(["git", "rev-list", f"{base}..{head}"], text=True).splitlines()
    if not commits:
        raise ValueError("DCO range is empty")
    failed = []
    for sha in commits:
        name, email, message = subprocess.check_output(
            ["git", "show", "-s", "--format=%an%x00%ae%x00%B", sha], text=True).split("\0", 2)
        if not valid_signoff(message, name, email):
            failed.append(sha)
    if failed:
        raise ValueError("Missing matching author DCO trailer: " + ", ".join(failed))
    return len(commits)


def main():
    print(f'DCO verified for {check(os.environ["DCO_BASE"], os.environ["DCO_HEAD"])} contribution commits.')


if __name__ == "__main__":
    main()
