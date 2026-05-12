import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "resume_matcher.db")


def get_db_path() -> str:
    return os.environ.get("SQLITE_PATH", DEFAULT_DB_PATH)


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    _ensure_parent_dir(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    _ensure_parent_dir(get_db_path())
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
                vacancy_id INTEGER NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
                final_score REAL NOT NULL,
                semantic_similarity REAL NOT NULL,
                llm_judge_score REAL NOT NULL,
                reasoning TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_analyses_resume ON analyses(resume_id);
            CREATE INDEX IF NOT EXISTS idx_analyses_vacancy ON analyses(vacancy_id);
            CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
            """
        )


def insert_resume(original_filename: str, extracted_text: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO resumes (original_filename, extracted_text) VALUES (?, ?)",
            (original_filename, extracted_text),
        )
        return int(cur.lastrowid)


def insert_vacancy(original_filename: str, extracted_text: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO vacancies (original_filename, extracted_text) VALUES (?, ?)",
            (original_filename, extracted_text),
        )
        return int(cur.lastrowid)


def get_resume(resume_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, original_filename, extracted_text, created_at FROM resumes WHERE id = ?",
            (resume_id,),
        ).fetchone()
        return dict(row) if row else None


def get_vacancy(vacancy_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, original_filename, extracted_text, created_at FROM vacancies WHERE id = ?",
            (vacancy_id,),
        ).fetchone()
        return dict(row) if row else None


def insert_analysis(
    resume_id: int,
    vacancy_id: int,
    final_score: float,
    semantic_similarity: float,
    llm_judge_score: float,
    reasoning: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses (
                resume_id, vacancy_id, final_score,
                semantic_similarity, llm_judge_score, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                vacancy_id,
                final_score,
                semantic_similarity,
                llm_judge_score,
                reasoning,
            ),
        )
        return int(cur.lastrowid)


def list_analyses_for_vacancy(vacancy_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id AS analysis_id,
                a.resume_id,
                a.vacancy_id,
                a.final_score,
                a.semantic_similarity,
                a.llm_judge_score,
                a.reasoning,
                a.created_at,
                r.original_filename AS resume_filename
            FROM analyses a
            INNER JOIN resumes r ON r.id = a.resume_id
            WHERE a.vacancy_id = ?
            ORDER BY a.created_at DESC, a.id DESC
            """,
            (vacancy_id,),
        ).fetchall()
        return [dict(row) for row in rows]

def delete_resume(resume_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))

def delete_vacancy(vacancy_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))

def delete_all_resumes() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM resumes")

def delete_all_vacancies() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM vacancies")
