"""Trusted receipts with out-of-manifest expected hashes and object identities."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from .sw3_formal_core import sha, write, verify


class Trust:
    def __init__(self, directory, run_id, writer, restricted_sid):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(exist_ok=False)
        self.run_id, self.writer, self.sid = run_id, writer, restricted_sid
        self.expected = {}

    def fix(self, gate, sequence, manifest_path, manifest, previous=None):
        if gate in self.expected or gate not in (1,2,3):
            raise ValueError("Invalid or duplicate trusted gate")
        if gate>1 and (previous is None or previous != self.expected[gate-1]["receipt_sha256"]):
            raise ValueError("Missing prior trusted anchor")
        verify(manifest)
        path = Path(manifest_path).resolve()
        if json.loads(path.read_bytes()) != manifest:
            raise ValueError("Manifest does not describe supplied inventory")
        receipt_path = self.directory / f"gate_{gate}.json"
        with receipt_path.open("x",encoding="utf-8"):
            pass
        receipt_id = receipt_path.stat().st_ino
        receipt = dict(run_id=self.run_id,gate=gate,sequence=sequence,nonce=uuid4().hex,
            manifest_path=str(path),manifest_sha256=sha(path),manifest_file_id=path.stat().st_ino,
            sealed_directory_file_id=path.parent.stat().st_ino,
            receipt_path=str(receipt_path),receipt_file_id=receipt_id,
            created=datetime.now(timezone.utc).isoformat(),writer=self.writer,
            restricted_sid=self.sid,previous_receipt_sha256=previous)
        receipt_path.write_text(json.dumps(receipt,sort_keys=True),encoding="utf-8")
        anchor=dict(receipt_path=str(receipt_path),receipt_sha256=sha(receipt_path),
                    receipt_file_id=receipt_id)
        self.expected[gate]=anchor
        return dict(anchor)

    def verify(self,gate):
        anchor=self.expected[gate]
        return verify_anchor(anchor)


def verify_anchor(anchor):
    receipt_path=Path(anchor["receipt_path"])
    if sha(receipt_path)!=anchor["receipt_sha256"] or receipt_path.stat().st_ino!=anchor["receipt_file_id"]:
        raise ValueError("Trusted receipt changed")
    r=json.loads(receipt_path.read_bytes())
    path=Path(r["manifest_path"])
    if (sha(path)!=r["manifest_sha256"] or path.stat().st_ino!=r["manifest_file_id"]
            or path.parent.stat().st_ino!=r["sealed_directory_file_id"]):
        raise ValueError("Anchored manifest changed")
    manifest=json.loads(path.read_bytes())
    verify(manifest)
    return manifest
