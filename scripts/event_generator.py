#!/usr/bin/env python3
"""
Event Generator for The Hobbit Journey Stream.

Generates narrative events by calling OpenRouter LLM for gap blocks,
persisting results in SQLite with full provenance logging.

Usage:
    python scripts/event_generator.py --gap-id gap_canon_044_canon_045 --days 3
    python scripts/event_generator.py --gap-id gap_canon_044_canon_045 --limit 10
    python scripts/event_generator.py --all-small-gaps --limit 50
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Ensure project root on path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from prompt_engine import PromptEngine, load_openrouter_config

DB_PATH = os.path.join(PROJECT_ROOT, "data", "generated_events.db")


def init_db(db_path: str = DB_PATH):
    """Initialize SQLite schema for events and generation batches."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            gap_id TEXT NOT NULL,
            phase_id TEXT,
            phase_title TEXT,
            day_number INTEGER,
            journey_day INTEGER,
            hour_of_day REAL,
            block_id TEXT NOT NULL,
            block_index INTEGER,
            prompt_system TEXT,
            prompt_user TEXT,
            content TEXT,
            model TEXT,
            provider TEXT,
            temperature REAL,
            max_tokens INTEGER,
            top_p REAL,
            frequency_penalty REAL,
            presence_penalty REAL,
            generation_time_ms INTEGER,
            created_at TEXT,
            request_hash TEXT,
            duration_hours REAL,
            batch_id TEXT,
            is_active INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_events_gap ON events(gap_id);
        CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_hash ON events(request_hash);

        CREATE TABLE IF NOT EXISTS generation_batches (
            batch_id TEXT PRIMARY KEY,
            gap_id TEXT,
            status TEXT NOT NULL,
            params_json TEXT,
            started_at TEXT,
            completed_at TEXT,
            events_generated INTEGER DEFAULT 0,
            error TEXT
        );

        CREATE TABLE IF NOT EXISTS generation_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            event_id TEXT,
            gap_id TEXT,
            status TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            error_message TEXT,
            logged_at TEXT
        );
        """
    )
    # Migrations for existing databases
    for col_sql in [
        "ALTER TABLE events ADD COLUMN journey_day INTEGER",
        "ALTER TABLE events ADD COLUMN hour_of_day REAL",
        "ALTER TABLE events ADD COLUMN is_active INTEGER DEFAULT 1",
        "ALTER TABLE events ADD COLUMN duration_hours REAL",
        "ALTER TABLE events ADD COLUMN batch_id TEXT",
    ]:
        try:
            conn.execute(col_sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
    conn.close()
    print(f"[DB] Initialized {db_path}")


def _request_hash(prompt_dict: dict) -> str:
    payload = json.dumps(prompt_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class EventGenerator:
    def __init__(self, db_path: str = DB_PATH, cfg_path: str = "config/openrouter.yaml", model_override: Optional[str] = None):
        self.db_path = db_path
        self.cfg = load_openrouter_config(cfg_path)
        self.engine = PromptEngine(cfg_path)
        self.model_override = model_override
        self._init_http()

    def _init_http(self):
        try:
            import requests
            self.session = requests.Session()
            self.has_requests = True
        except ImportError:
            self.session = None
            self.has_requests = False

    def _call_llm(self, prompt_dict: dict) -> Dict[str, Any]:
        if not self.has_requests:
            raise RuntimeError("The 'requests' package is required. Install it with: pip install requests")

        api_key = self.cfg.get("api_key", "")
        if not api_key or api_key.startswith("${"):
            raise RuntimeError("OpenRouter API key not configured. Set OPENROUTER_API_KEY env var.")

        base_url = self.cfg.get("base_url", "https://openrouter.ai/api/v1")
        model = prompt_dict.get("model", self.cfg.get("default_model", "openai/gpt-4o-mini"))

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hobbit-journey.local",
            "X-Title": "Hobbit Journey Stream",
        }

        payload = {
            "model": model,
            "messages": prompt_dict["messages"],
            "temperature": prompt_dict.get("temperature", 0.85),
            "max_tokens": prompt_dict.get("max_tokens", 256),
            "top_p": prompt_dict.get("top_p", 0.95),
            "frequency_penalty": prompt_dict.get("frequency_penalty", 0.2),
            "presence_penalty": prompt_dict.get("presence_penalty", 0.1),
        }

        retries = self.cfg.get("retries", {}).get("max_attempts", 3)
        backoff = self.cfg.get("retries", {}).get("backoff_seconds", 2)
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                resp = self.session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "ok": True,
                    "content": data["choices"][0]["message"]["content"],
                    "model_used": data.get("model", model),
                    "usage": data.get("usage", {}),
                    "raw": data,
                }
            except Exception as e:
                last_error = str(e)
                print(f"[LLM] Attempt {attempt}/{retries} failed: {last_error}")
                if attempt < retries:
                    time.sleep(backoff * attempt)

        return {"ok": False, "error": last_error}

    def generate_block(
        self,
        block: dict,
        batch_id: str,
        block_index: int,
        dry_run: bool = False,
    ) -> Optional[str]:
        gap_id = block["gap_id"]
        prompt = self.engine.compose(
            gap_id=gap_id,
            block=block,
            day_number=block["day_number"],
            hour_of_day=block["hour_start"],
            phase_meta={"title": block.get("phase_title"), "mood": block.get("mood")},
            model_override=self.model_override,
        )

        req_hash = _request_hash(prompt)
        event_id = str(uuid.uuid4())
        timestamp = block["timestamp"]
        model = prompt.get("model")

        conn = sqlite3.connect(self.db_path)
        # Check for existing exact hash to avoid regeneration
        if not dry_run:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM events WHERE request_hash = ?", (req_hash,))
            row = cur.fetchone()
            conn.row_factory = None
            if row:
                print(f"  [Cache] Hit for hash {req_hash}")
                old = dict(row)
                cached_id = str(uuid.uuid4())
                journey_day = block.get("journey_day") if block.get("journey_day") is not None else old.get("journey_day")
                hour_of_day = block.get("hour_start") if block.get("hour_start") is not None else old.get("hour_of_day")
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, timestamp, gap_id, phase_id, phase_title, day_number, journey_day, hour_of_day, duration_hours, block_id, block_index,
                        prompt_system, prompt_user, content, model, provider, temperature, max_tokens, top_p,
                        frequency_penalty, presence_penalty, generation_time_ms, created_at, request_hash,
                        batch_id, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cached_id,
                        old.get("timestamp"),
                        old.get("gap_id"),
                        old.get("phase_id"),
                        old.get("phase_title"),
                        old.get("day_number"),
                        journey_day,
                        hour_of_day,
                        old.get("duration_hours"),
                        old.get("block_id"),
                        old.get("block_index"),
                        old.get("prompt_system"),
                        old.get("prompt_user"),
                        old.get("content"),
                        old.get("model"),
                        old.get("provider"),
                        old.get("temperature"),
                        old.get("max_tokens"),
                        old.get("top_p"),
                        old.get("frequency_penalty"),
                        old.get("presence_penalty"),
                        old.get("generation_time_ms"),
                        old.get("created_at"),
                        old.get("request_hash"),
                        batch_id,
                        1,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO generation_logs (batch_id, event_id, gap_id, status, model, logged_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (batch_id, cached_id, gap_id, "cached", model, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
                )
                conn.commit()
                conn.close()
                return cached_id

        if dry_run:
            print(f"  [Dry-run] Would generate {block['block_id']} at {timestamp}")
            conn.close()
            return None

        print(f"  [Generate] {block['block_id']} at {timestamp} -> {model}")
        start = time.time()
        result = self._call_llm(prompt)
        elapsed_ms = int((time.time() - start) * 1000)

        usage = result.get("usage", {})
        if result["ok"]:
            content = result["content"]
            conn.execute(
                """
                INSERT INTO events (
                    event_id, timestamp, gap_id, phase_id, phase_title, day_number, journey_day, hour_of_day, duration_hours, block_id, block_index,
                    prompt_system, prompt_user, content, model, provider, temperature, max_tokens, top_p,
                    frequency_penalty, presence_penalty, generation_time_ms, created_at, request_hash,
                    batch_id, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    timestamp,
                    gap_id,
                    block.get("phase_id"),
                    block.get("phase_title"),
                    block.get("day_number"),
                    block.get("journey_day"),
                    block.get("hour_start"),
                    block.get("duration_hours"),
                    block.get("block_id"),
                    block_index,
                    prompt["messages"][0]["content"],
                    prompt["messages"][1]["content"],
                    content,
                    result.get("model_used", model),
                    "openrouter",
                    prompt.get("temperature"),
                    prompt.get("max_tokens"),
                    prompt.get("top_p"),
                    prompt.get("frequency_penalty"),
                    prompt.get("presence_penalty"),
                    elapsed_ms,
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    req_hash,
                    batch_id,
                    1,
                ),
            )
            conn.execute(
                """
                INSERT INTO generation_logs
                (batch_id, event_id, gap_id, status, model, prompt_tokens, completion_tokens, total_tokens, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    event_id,
                    gap_id,
                    "success",
                    result.get("model_used", model),
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                ),
            )
            conn.commit()
            conn.close()
            return event_id
        else:
            conn.execute(
                """
                INSERT INTO generation_logs
                (batch_id, event_id, gap_id, status, model, error_message, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_id, event_id, gap_id, "error", model, result.get("error"), datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            )
            conn.commit()
            conn.close()
            print(f"  [Error] {result.get('error')}")
            return None

    def generate_gap(
        self,
        gap_id: str,
        max_blocks: Optional[int] = None,
        days: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        batch_id = str(uuid.uuid4())
        print(f"\n[Batch {batch_id}] Starting generation for {gap_id}")

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO generation_batches (batch_id, gap_id, status, params_json, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                gap_id,
                "running",
                json.dumps({"max_blocks": max_blocks, "days": days, "dry_run": dry_run}),
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            ),
        )
        # Deactivate previous active events for this gap so the new batch becomes the default visible one
        conn.execute(
            "UPDATE events SET is_active = 0 WHERE gap_id = ? AND is_active = 1",
            (gap_id,)
        )
        conn.commit()
        conn.close()

        blocks = self.engine.expand_gap_blocks(gap_id)

        # Filter by days if requested
        if days is not None:
            original_count = len(blocks)
            max_block_day = max((b["day_number"] for b in blocks), default=0)
            blocks = [b for b in blocks if b["day_number"] <= days]
            print(f"[Batch {batch_id}] Day filter: {len(blocks)}/{original_count} blocks kept (max day was {max_block_day}, limit={days})")
            # Hard runtime guard: break loop if any block somehow exceeds the limit
            for b in blocks:
                if b["day_number"] > days:
                    raise ValueError(f"Block {b['block_id']} day_number {b['day_number']} exceeds limit {days}")

        if max_blocks is not None:
            blocks = blocks[:max_blocks]

        total = len(blocks)
        print(f"[Batch {batch_id}] {total} blocks to generate")

        generated = 0
        errors = 0
        for idx, block in enumerate(blocks):
            event_id = self.generate_block(block, batch_id=batch_id, block_index=idx, dry_run=dry_run)
            if event_id:
                generated += 1
            elif not dry_run:
                errors += 1

            # Simple rate limiting
            rpm = self.cfg.get("rate_limit_rpm", 60)
            if rpm > 0 and not dry_run:
                time.sleep(60.0 / rpm)

        status = "completed" if errors == 0 else "partial" if generated > 0 else "failed"
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            UPDATE generation_batches
            SET status = ?, completed_at = ?, events_generated = ?
            WHERE batch_id = ?
            """,
            (status, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), generated, batch_id),
        )
        conn.commit()
        conn.close()

        summary = {"batch_id": batch_id, "gap_id": gap_id, "total_blocks": total, "generated": generated, "errors": errors, "status": status}
        print(f"[Batch {batch_id}] Done: {summary}")
        self._notify_hook(summary)
        return summary

    def _notify_hook(self, payload: dict):
        try:
            import urllib.request, json
            req = urllib.request.Request(
                "http://localhost:5000/api/events/hook",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            # Silently ignore if server is not running
            pass


def main():
    parser = argparse.ArgumentParser(description="Generate narrative events for Hobbit Journey gaps")
    parser.add_argument("--gap-id", help="Specific gap ID to generate")
    parser.add_argument("--days", type=int, help="Limit to first N days of the gap")
    parser.add_argument("--limit", type=int, help="Limit total number of blocks generated")
    parser.add_argument("--dry-run", action="store_true", help="Expand blocks without calling LLM")
    parser.add_argument("--all-small-gaps", action="store_true", help="Generate for all small gaps")
    parser.add_argument("--all-travel-gaps", action="store_true", help="Generate for all travel gaps")
    parser.add_argument("--all-micro-gaps", action="store_true", help="Generate for all micro gaps")
    parser.add_argument("--init-db", action="store_true", help="Initialize DB and exit")
    parser.add_argument("--model", help="Override the LLM model for this run (e.g. anthropic/claude-3.5-sonnet)")
    args = parser.parse_args()

    init_db()
    if args.init_db:
        return

    gen = EventGenerator(model_override=args.model)

    if args.gap_id:
        gen.generate_gap(args.gap_id, max_blocks=args.limit, days=args.days, dry_run=args.dry_run)
        return

    # Batch modes
    gaps = gen.engine.resolver.gap_plans["gaps"]
    targets = []
    if args.all_small_gaps:
        targets += [g["gap_id"] for g in gaps if g["gap_type"] == "small"]
    if args.all_travel_gaps:
        targets += [g["gap_id"] for g in gaps if g["gap_type"] == "travel"]
    if args.all_micro_gaps:
        targets += [g["gap_id"] for g in gaps if g["gap_type"] == "micro"]

    if not targets:
        print("No targets specified. Use --gap-id, --all-small-gaps, --all-travel-gaps, or --all-micro-gaps")
        parser.print_help()
        return

    for gap_id in targets:
        gen.generate_gap(gap_id, max_blocks=args.limit, days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
