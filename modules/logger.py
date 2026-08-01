"""Central logging for JARVIS — all progress saved automatically."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path


class JarvisLogger:
    def __init__(self, root: Path):
        self.root = root
        self.log_dir = root / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"jarvis_{stamp}.log"
        self.events_file = self.log_dir / f"events_{stamp}.jsonl"

        self.logger = logging.getLogger("JARVIS")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%H:%M:%S")
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warn(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def event(self, kind: str, data: dict | None = None) -> None:
        payload = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "kind": kind,
            "data": data or {},
        }
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.info(f"{kind}: {data or {}}")
