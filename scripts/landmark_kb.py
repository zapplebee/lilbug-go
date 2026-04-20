"""SQLite landmark knowledge base for Lilbug room observations."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS landmarks (
    tag_id INTEGER PRIMARY KEY,
    label TEXT NOT NULL,
    zone TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'known'
);

CREATE TABLE IF NOT EXISTS handoffs (
    from_tag INTEGER NOT NULL,
    to_tag INTEGER NOT NULL,
    reverse_ms INTEGER,
    search_direction TEXT,
    blind_turn_ms INTEGER,
    confidence REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    PRIMARY KEY (from_tag, to_tag)
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id INTEGER,
    snapshot_path TEXT,
    center_x REAL,
    center_y REAL,
    side_px REAL,
    decision_margin REAL,
    visible_tags TEXT,
    depth_warning INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


SEED_LANDMARKS = {
    0: {
        "label": "blue_bin",
        "zone": "fridge_doorway",
        "notes": "Blue bin/cooler near refrigerator and doorway.",
        "status": "confirmed",
    },
    1: {
        "label": "tv_bin",
        "zone": "fireplace_tv",
        "notes": "Black bin under TV stand beside stone fireplace.",
        "status": "confirmed",
    },
    3: {"label": "tag_3", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
    4: {"label": "tag_4", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
    5: {"label": "tag_5", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
    6: {"label": "tag_6", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
    7: {"label": "tag_7", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
    8: {"label": "tag_8", "zone": "unknown", "notes": "Not yet located.", "status": "unconfirmed"},
}


SEED_HANDOFFS = {
    (1, 0): {
        "reverse_ms": 700,
        "search_direction": "left",
        "blind_turn_ms": 0,
        "confidence": 0.8,
        "notes": "Validated live multiple times in current room.",
    },
    (0, 1): {
        "reverse_ms": 700,
        "search_direction": "right",
        "blind_turn_ms": 0,
        "confidence": 0.8,
        "notes": "Validated live multiple times in current room.",
    },
}


class LandmarkKB:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.seed_defaults()

    def seed_defaults(self) -> None:
        for tag_id, row in SEED_LANDMARKS.items():
            self.conn.execute(
                """
                INSERT INTO landmarks(tag_id, label, zone, notes, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(tag_id) DO UPDATE SET
                    label=excluded.label,
                    zone=COALESCE(landmarks.zone, excluded.zone),
                    notes=COALESCE(landmarks.notes, excluded.notes),
                    status=CASE WHEN landmarks.status = 'confirmed' THEN landmarks.status ELSE excluded.status END
                """,
                (tag_id, row["label"], row["zone"], row["notes"], row["status"]),
            )
        for (from_tag, to_tag), row in SEED_HANDOFFS.items():
            self.conn.execute(
                """
                INSERT INTO handoffs(from_tag, to_tag, reverse_ms, search_direction, blind_turn_ms, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_tag, to_tag) DO NOTHING
                """,
                (
                    from_tag,
                    to_tag,
                    row["reverse_ms"],
                    row["search_direction"],
                    row["blind_turn_ms"],
                    row["confidence"],
                    row["notes"],
                ),
            )
        self.conn.commit()

    def landmark(self, tag_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM landmarks WHERE tag_id = ?", (tag_id,)).fetchone()

    def handoff(self, from_tag: int, to_tag: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM handoffs WHERE from_tag = ? AND to_tag = ?",
            (from_tag, to_tag),
        ).fetchone()

    def visible_known_tags(self) -> list[int]:
        rows = self.conn.execute("SELECT tag_id FROM landmarks WHERE status = 'confirmed' ORDER BY tag_id").fetchall()
        return [int(row[0]) for row in rows]

    def record_observation(
        self,
        *,
        tag_id: int | None,
        snapshot_path: str,
        center_x: float | None,
        center_y: float | None,
        side_px: float | None,
        decision_margin: float | None,
        visible_tags: str,
        depth_warning: bool,
        note: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO observations(tag_id, snapshot_path, center_x, center_y, side_px, decision_margin, visible_tags, depth_warning, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tag_id,
                snapshot_path,
                center_x,
                center_y,
                side_px,
                decision_margin,
                visible_tags,
                1 if depth_warning else 0,
                note,
            ),
        )
        self.conn.commit()

    def confirm_landmark(self, tag_id: int, zone: str | None, notes: str | None) -> None:
        self.conn.execute(
            """
            UPDATE landmarks
            SET zone = COALESCE(?, zone),
                notes = CASE WHEN ? IS NULL OR ? = '' THEN notes ELSE ? END,
                status = 'confirmed'
            WHERE tag_id = ?
            """,
            (zone, notes, notes, notes, tag_id),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
