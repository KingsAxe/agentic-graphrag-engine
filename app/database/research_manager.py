import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from typing import List, Optional

class ResearchManager:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    def save_entry(self, session_id: str, query: str, response_obj) -> int:
        """
        Crystallizes a ResearchResponse into the database.
        response_obj is the Pydantic ResearchResponse from rag_chain.py
        """
        sql = """
            INSERT INTO research_entries 
            (session_id, query_text, answer_text, epistemic_score, reasoning_path, citations, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        
        # Convert Pydantic/Lists to JSON for Postgres JSONB column
        citations_json = json.dumps(response_obj.citations)
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        session_id,
                        query,
                        response_obj.answer,
                        response_obj.belief_report.epistemic_score,
                        response_obj.belief_report.reasoning_process,
                        citations_json,
                        'pending'
                    ))
                    entry_id = cur.fetchone()['id']
                    conn.commit()
                    return entry_id
        except Exception as e:
            print(f"Error saving research entry: {e}")
            return -1

    def verify_entry(self, entry_id: int, status: str, notes: Optional[str] = None):
        """Updates the status of an entry (verified/rejected) and adds notes."""
        sql = """
            UPDATE research_entries 
            SET verification_status = %s, user_notes = %s 
            WHERE id = %s;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (status, notes, entry_id))
                    conn.commit()
        except Exception as e:
            print(f"Error verifying research entry: {e}")

    def get_session_entries(self, session_id: str) -> List[dict]:
        """Fetches all entries for the current research session."""
        sql = "SELECT * FROM research_entries WHERE session_id = %s ORDER BY created_at DESC;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (session_id,))
                    return cur.fetchall()
        except Exception as e:
            print(f"Error fetching entries: {e}")
            return []

    def get_verified_knowledge(self, session_id: str) -> str:
        """
        Retrieves all 'verified' answers to be injected into the LLM context.
        This is the 'Recursive Knowledge' feature.
        """
        sql = "SELECT query_text, answer_text FROM research_entries WHERE session_id = %s AND verification_status = 'verified';"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (session_id,))
                    rows = cur.fetchall()
                    context_snippet = "\n".join([f"Q: {r['query_text']}\nA: {r['answer_text']}" for r in rows])
                    return context_snippet
        except Exception as e:
            print(f"Error fetching verified knowledge: {e}")
            return ""