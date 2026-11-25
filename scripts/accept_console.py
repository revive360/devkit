#!/usr/bin/env python3
"""Apply recorded hardware acceptance to the exact existing development package.

Offline metadata update only: no console access, build or source relabeling.
"""
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/console-acceptance-2026-11-25.json"


def apply_acceptance(manifest: dict, record: dict) -> dict:
    if record["console_validation"] != "accepted" or record["evidence_kind"] != "owner-and-coordinator-report":
        raise ValueError("An explicit owner/coordinator acceptance record is required")
    date.fromisoformat(record["accepted_on"])
    if manifest["source_commit"] != record["source_commit"] or manifest["xex_sha256"] != record["xex_sha256"]:
        raise ValueError("Console acceptance does not match this source commit and binary hash")
    return {**manifest, "console_validation": "accepted",
            "console_validation_date": record["accepted_on"],
            "console_validation_record": record}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    record = json.loads(RECORD.read_text())
    package = ROOT / "dist/hello"
    manifest = json.loads((package / "manifest.json").read_text())
    build_path = ROOT / "build/xbox/build.json"
    build = json.loads(build_path.read_text())
    # Validate the complete existing package and both binary copies before writes.
    for name, expected in manifest["files_sha256"].items():
        if digest((package / name).read_bytes()) != expected:
            raise ValueError(f"Existing packaged file differs from its manifest: {name}")
    for binary in (package / "default.xex", ROOT / "build/xbox/hello.xex"):
        if digest(binary.read_bytes()) != record["xex_sha256"]:
            raise ValueError("Tested XEX hash does not match the existing package/build")
    accepted = apply_acceptance(manifest, record)
    accepted_build = apply_acceptance(build, record)
    archive = ROOT / "dist/hello-development.zip"
    with zipfile.ZipFile(archive) as original:
        old_members = {name:original.read(name) for name in original.namelist()}
    if old_members.get("hello/manifest.json") != (package / "manifest.json").read_bytes():
        raise ValueError("Archive manifest differs from the package directory")
    for name, expected in manifest["files_sha256"].items():
        if digest(old_members["hello/"+name]) != expected:
            raise ValueError("Archive payload differs from its manifest")
    files = {name:(package/name).read_bytes() for name in manifest["files_sha256"]}
    start = files["START-HERE.txt"].decode()
    original_notice = "Real-console validation is PENDING. This is not a tested release."
    accepted_notice = ("Real-console validation ACCEPTED on 2026-11-25 for the recorded XEX hash,\n"
                       "on one Xbox 360 E (Corona), BadUpdate + Aurora, by the coordinator and owner.\n"
                       "See console-acceptance.json for results and limits. Future builds need new acceptance.\n"
                       "This is still a development artifact, not an organization CI-signed release.\n"
                       "source.tar retains the original R1 source commit and its historical documentation.")
    files["START-HERE.txt"] = start.replace(original_notice, accepted_notice).encode()
    files["console-acceptance.json"] = RECORD.read_bytes()
    accepted["files_sha256"] = {name:digest(data) for name,data in sorted(files.items())}
    files["manifest.json"] = (json.dumps(accepted,indent=2)+"\n").encode()
    evidence = ROOT / ".work/evidence"
    evidence.mkdir(parents=True,exist_ok=True)
    backup = evidence / f"hello-development-before-acceptance-{digest(archive.read_bytes())}.zip"
    if not backup.exists():
        shutil.copyfile(archive,backup)
    for name,data in files.items():
        (package/name).write_bytes(data)
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as output:
        for name,data in sorted(files.items()):
            entry=zipfile.ZipInfo("hello/"+name,date_time=(2026,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o100644 << 16
            output.writestr(entry,data)
    build_path.write_text(json.dumps(accepted_build,indent=2)+"\n")
    (ROOT/"dist/SHA256SUMS").write_text(f'{digest(archive.read_bytes())}  {archive.name}\n{record["xex_sha256"]}  hello/default.xex\n')
    print(f'Console acceptance recorded. XEX unchanged: {record["xex_sha256"]}')
    print(f'Updated development ZIP: {digest(archive.read_bytes())}')


if __name__ == "__main__":
    main()
