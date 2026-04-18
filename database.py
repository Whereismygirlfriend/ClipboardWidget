import sqlite3
import threading

SQLITE_IN_CLAUSE_LIMIT = 900


class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clips (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT,
                    is_duplicate INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON clips(timestamp DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_content_hash ON clips(content_hash)"
            )
            self.conn.commit()

    def insert_clip(
        self,
        record_id,
        c_type,
        content,
        c_hash,
        is_duplicate,
        timestamp=None,
    ):
        with self.lock:
            cursor = self.conn.cursor()
            if timestamp is None:
                cursor.execute(
                    """
                    INSERT INTO clips (id, type, content, content_hash, is_duplicate)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (record_id, c_type, content, c_hash, is_duplicate),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO clips (id, type, content, content_hash, is_duplicate, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (record_id, c_type, content, c_hash, is_duplicate, timestamp),
                )
            self.conn.commit()

    def _build_filter_clause(self, type_filter="all", duplicate_filter="all", search_keyword=""):
        clauses = []
        params = []

        if type_filter in ("text", "image", "file"):
            clauses.append("type = ?")
            params.append(type_filter)

        if duplicate_filter == "only":
            clauses.append("is_duplicate = 1")
        elif duplicate_filter == "exclude":
            clauses.append("is_duplicate = 0")

        keyword = str(search_keyword or "").strip()
        if keyword:
            clauses.append("content LIKE ?")
            params.append(f"%{keyword}%")

        where_clause = ""
        if clauses:
            where_clause = " WHERE " + " AND ".join(clauses)
        return where_clause, params

    def count_clips(self, type_filter="all", duplicate_filter="all", search_keyword=""):
        where_clause, params = self._build_filter_clause(
            type_filter=type_filter,
            duplicate_filter=duplicate_filter,
            search_keyword=search_keyword,
        )
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(1) AS count FROM clips{where_clause}", params)
            row = cursor.fetchone()
            return int(row["count"]) if row else 0

    def get_clips(
        self,
        limit,
        offset=0,
        type_filter="all",
        duplicate_filter="all",
        search_keyword="",
    ):
        where_clause, params = self._build_filter_clause(
            type_filter=type_filter,
            duplicate_filter=duplicate_filter,
            search_keyword=search_keyword,
        )
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                SELECT id, type, content, timestamp, is_duplicate
                FROM clips
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """,
                [*params, limit, offset],
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_clips(self, type_filter="all", duplicate_filter="all", search_keyword=""):
        return self.get_clips(
            limit=self.count_clips(
                type_filter=type_filter,
                duplicate_filter=duplicate_filter,
                search_keyword=search_keyword,
            ),
            offset=0,
            type_filter=type_filter,
            duplicate_filter=duplicate_filter,
            search_keyword=search_keyword,
        )

    def get_clip_ids(
        self,
        type_filter="all",
        duplicate_filter="all",
        search_keyword="",
        limit=None,
        offset=0,
    ):
        where_clause, params = self._build_filter_clause(
            type_filter=type_filter,
            duplicate_filter=duplicate_filter,
            search_keyword=search_keyword,
        )
        sql = f"""
            SELECT id
            FROM clips
            {where_clause}
            ORDER BY timestamp DESC
        """
        query_params = list(params)
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            query_params.extend([int(limit), int(offset)])

        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, query_params)
            return [row["id"] for row in cursor.fetchall()]

    def get_clips_by_ids(self, clip_ids):
        if not clip_ids:
            return []

        normalized_ids = [str(cid) for cid in clip_ids if str(cid).strip()]
        if not normalized_ids:
            return []

        with self.lock:
            cursor = self.conn.cursor()
            rows = []
            for idx in range(0, len(normalized_ids), SQLITE_IN_CLAUSE_LIMIT):
                chunk = normalized_ids[idx : idx + SQLITE_IN_CLAUSE_LIMIT]
                placeholders = ",".join("?" for _ in chunk)
                cursor.execute(
                    f"""
                    SELECT id, type, content, timestamp, is_duplicate
                    FROM clips
                    WHERE id IN ({placeholders})
                """,
                    chunk,
                )
                rows.extend(dict(row) for row in cursor.fetchall())
            rows.sort(key=lambda row: row.get("timestamp", ""), reverse=True)
            return rows

    def check_exists_by_hash(self, c_hash, session_start_time):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM clips
                WHERE content_hash = ? AND timestamp >= ?
                LIMIT 1
            """,
                (c_hash, session_start_time),
            )
            return cursor.fetchone() is not None

    def get_existing_hashes_since(self, hashes, since_timestamp):
        normalized_hashes = [str(h).strip() for h in hashes if str(h).strip()]
        if not normalized_hashes:
            return set()

        existing = set()
        with self.lock:
            cursor = self.conn.cursor()
            for idx in range(0, len(normalized_hashes), SQLITE_IN_CLAUSE_LIMIT):
                chunk = normalized_hashes[idx : idx + SQLITE_IN_CLAUSE_LIMIT]
                placeholders = ",".join("?" for _ in chunk)
                cursor.execute(
                    f"""
                    SELECT DISTINCT content_hash
                    FROM clips
                    WHERE timestamp >= ? AND content_hash IN ({placeholders})
                """,
                    [since_timestamp, *chunk],
                )
                existing.update(
                    row["content_hash"]
                    for row in cursor.fetchall()
                    if row["content_hash"]
                )
        return existing

    def insert_clips_bulk(self, records):
        if not records:
            return 0
        with self.lock:
            cursor = self.conn.cursor()
            cursor.executemany(
                """
                INSERT INTO clips (id, type, content, content_hash, is_duplicate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                records,
            )
            self.conn.commit()
            return len(records)

    def delete_clips(self, clip_ids):
        if not clip_ids:
            return []

        normalized_ids = [str(cid) for cid in clip_ids if str(cid).strip()]
        if not normalized_ids:
            return []

        with self.lock:
            cursor = self.conn.cursor()
            removed = []
            for idx in range(0, len(normalized_ids), SQLITE_IN_CLAUSE_LIMIT):
                chunk = normalized_ids[idx : idx + SQLITE_IN_CLAUSE_LIMIT]
                placeholders = ",".join("?" for _ in chunk)
                cursor.execute(
                    f"""
                    SELECT id, type, content
                    FROM clips
                    WHERE id IN ({placeholders})
                """,
                    chunk,
                )
                removed.extend(dict(row) for row in cursor.fetchall())
            cursor.executemany(
                "DELETE FROM clips WHERE id = ?",
                [(cid,) for cid in normalized_ids],
            )
            self.conn.commit()
            return removed

    def close(self):
        with self.lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
