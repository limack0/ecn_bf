import sqlite3
import streamlit as st
import json
from typing import Dict
from datetime import datetime, date


class DatabaseManager:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Pour obtenir des dictionnaires
            return conn
        except Exception as e:
            st.error(f"Erreur de connexion à la base de données: {e}")
            return None

    def init_database(self):
        conn = self.get_connection()
        if conn is None:
            return False

        try:
            cur = conn.cursor()

            # Table users
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    specialty TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table scores
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    specialty TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    time_taken INTEGER,
                    case_title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Table badges
            cur.execute("""
                CREATE TABLE IF NOT EXISTS badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    badge_type TEXT NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Table clinical_cases
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clinical_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    specialty TEXT NOT NULL,
                    title TEXT NOT NULL,
                    case_data TEXT NOT NULL,
                    difficulty TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table ecn_simulations
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ecn_simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    simulation_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    max_score REAL NOT NULL,
                    percentage REAL NOT NULL,
                    duration INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    simulation_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
            return True

        except Exception as e:
            st.error(f"Erreur lors de l'initialisation: {e}")
            return False
        finally:
            conn.close()

    def get_or_create_user(self, username: str, specialty: str = "general"):
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cur.fetchone()

            if result:
                return result["id"]

            email = f"{username}@ecn-prep.fr"
            cur.execute(
                "INSERT INTO users (username, email, specialty) VALUES (?, ?, ?)",
                (username, email, specialty),
            )
            conn.commit()
            return cur.lastrowid

        except Exception as e:
            print(f"❌ Erreur get_or_create_user: {e}")
            return None
        finally:
            conn.close()

    def save_score(self, username, specialty, score, total_questions, time_taken):
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()
            user_id = self.get_or_create_user(username, specialty)

            cur.execute("""
                INSERT INTO scores (user_id, specialty, score, total_questions, time_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, specialty, score, total_questions, time_taken))

            conn.commit()
            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {e}")
            return False
        finally:
            conn.close()

    def get_leaderboard(self, specialty=None, limit=10):
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            if specialty:
                cur.execute("""
                    SELECT u.username, SUM(s.score) as total_score, COUNT(s.id) as quizzes_taken
                    FROM scores s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.specialty = ?
                    GROUP BY u.username
                    ORDER BY total_score DESC
                    LIMIT ?
                """, (specialty, limit))
            else:
                cur.execute("""
                    SELECT u.username, SUM(s.score) as total_score, COUNT(s.id) as quizzes_taken
                    FROM scores s
                    JOIN users u ON s.user_id = u.id
                    GROUP BY u.username
                    ORDER BY total_score DESC
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            st.error(f"Erreur lors de la récupération du classement: {e}")
            return []
        finally:
            conn.close()

    def get_user_progress_data(self, username: str):
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT s.specialty, AVG(s.score) as avg_score, COUNT(*) as quiz_count,
                    SUM(s.score) as total_score, AVG(s.time_taken) as avg_time
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE u.username = ?
                GROUP BY s.specialty
                ORDER BY avg_score DESC
            """, (username,))
            specialty_data = [dict(row) for row in cur.fetchall()]

            cur.execute("""
                SELECT DATE(s.created_at) as date, AVG(s.score) as daily_avg,
                    COUNT(*) as daily_quizzes
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE u.username = ?
                GROUP BY DATE(s.created_at)
                ORDER BY date
            """, (username,))
            timeline_data = [dict(row) for row in cur.fetchall()]

            return {
                "by_specialty": specialty_data,
                "timeline": timeline_data
            }
        except Exception as e:
            print(f"Erreur analytics: {e}")
            return None
        finally:
            conn.close()

    def save_ecn_simulation(self, username: str, simulation_data: Dict):
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()
            user_id = self.get_or_create_user(username)
            if not user_id:
                return False

            session = simulation_data["session"]
            results = simulation_data["results"]

            serializable_data = {
                "session_id": session["id"],
                "session_title": session["title"],
                "total_questions": session["total_questions"],
                "results_summary": results,
                "timestamp": datetime.now().isoformat(),
            }

            cur.execute("""
                INSERT INTO ecn_simulations 
                (user_id, simulation_id, score, max_score, percentage, duration, passed, grade, simulation_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session["id"],
                float(results["raw_score"]),
                float(results["max_score"]),
                float(results["percentage"]),
                int(simulation_data.get("time_taken", 0)),
                int(results["passed"]),
                results["grade"],
                json.dumps(serializable_data),
            ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Erreur sauvegarde simulation: {e}")
            return False
        finally:
            conn.close()

    def get_ecn_leaderboard(self, limit: int = 20):
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    u.username,
                    ROUND(AVG(e.percentage), 2) as avg_score,
                    ROUND(MAX(e.percentage), 2) as best_score,
                    COUNT(e.id) as simulations_count,
                    MIN(e.created_at) as first_simulation,
                    MAX(e.created_at) as last_simulation
                FROM ecn_simulations e
                JOIN users u ON e.user_id = u.id
                GROUP BY u.id, u.username
                ORDER BY best_score DESC, avg_score DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Erreur classement ECN: {e}")
            return []
        finally:
            conn.close()
