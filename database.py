import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from config import DatabaseConfig
from typing import Dict
import json
from datetime import datetime
import time

class DatabaseManager:
    def __init__(self):
        self.config = DatabaseConfig()
        self.max_retries = 3
    
    def get_connection(self):
        """Établit une connexion avec Neon - avec gestion des reconnexions"""
        for attempt in range(self.max_retries):
            try:
                conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    sslmode=self.config.sslmode,
                    connect_timeout=10
                )
                return conn
            except Exception as e:
                st.error(f"Tentative {attempt + 1}/{self.max_retries} - Erreur de connexion: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Attendre avant de réessayer
                else:
                    st.error("❌ Impossible de se connecter à la base de données")
                    return None
    
    def init_database(self):
        conn = self.get_connection()
        if conn is None:
            return False
        
        try:
            with conn.cursor() as cur:
                # Table des utilisateurs
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        specialty VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table des scores
                # Dans la méthode init_database(), modifiez la table scores :
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS scores (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        specialty VARCHAR(100) NOT NULL,
                        score INTEGER NOT NULL,
                        total_questions INTEGER NOT NULL,
                        time_taken INTEGER,
                        case_title VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table des badges
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS badges (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        badge_type VARCHAR(100) NOT NULL,
                        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table des dossiers cliniques
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clinical_cases (
                        id SERIAL PRIMARY KEY,
                        specialty VARCHAR(100) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        case_data JSONB NOT NULL,
                        difficulty VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """),
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ecn_simulations (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        simulation_id VARCHAR(255) NOT NULL,
                        score DECIMAL(5,2) NOT NULL,
                        max_score DECIMAL(5,2) NOT NULL,
                        percentage DECIMAL(5,2) NOT NULL,
                        duration INTEGER NOT NULL,
                        passed BOOLEAN NOT NULL,
                        grade VARCHAR(50) NOT NULL,
                        simulation_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                return True
                
        except Exception as e:
            st.error(f"Erreur lors de l'initialisation: {e}")
            return False
        finally:
            conn.close()
    
    def save_score(self, username, specialty, score, total_questions, time_taken):
        conn = self.get_connection()
        if conn is None:
            return False
        
        try:
            with conn.cursor() as cur:
                # Récupérer ou créer l'utilisateur
                cur.execute(
                    "INSERT INTO users (username, email, specialty) VALUES (%s, %s, %s) ON CONFLICT (username) DO UPDATE SET specialty = EXCLUDED.specialty RETURNING id",
                    (username, f"{username}@ecn.fr", specialty)
                )
                user_id = cur.fetchone()[0]
                
                # Sauvegarder le score
                cur.execute(
                    "INSERT INTO scores (user_id, specialty, score, total_questions, time_taken) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, specialty, score, total_questions, time_taken)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {e}")
            return False
        finally:
            conn.close()
    
    def get_leaderboard(self, specialty=None, limit=10):
        conn = self.get_connection()
        if conn is None:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if specialty:
                    query = """
                        SELECT u.username, SUM(s.score) as total_score, COUNT(s.id) as quizzes_taken
                        FROM scores s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.specialty = %s
                        GROUP BY u.username
                        ORDER BY total_score DESC
                        LIMIT %s
                    """
                    cur.execute(query, (specialty, limit))
                else:
                    query = """
                        SELECT u.username, SUM(s.score) as total_score, COUNT(s.id) as quizzes_taken
                        FROM scores s
                        JOIN users u ON s.user_id = u.id
                        GROUP BY u.username
                        ORDER BY total_score DESC
                        LIMIT %s
                    """
                    cur.execute(query, (limit,))
                
                return cur.fetchall()
                
        except Exception as e:
            st.error(f"Erreur lors de la récupération du classement: {e}")
            return []
        finally:
            conn.close()
    
    def get_user_progress_data(self, username: str):
        """Récupère les données de progression d'un utilisateur - VERSION CORRIGÉE"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                # Scores par spécialité - REQUÊTE CORRIGÉE
                cur.execute("""
                    SELECT s.specialty, AVG(s.score) as avg_score, COUNT(*) as quiz_count,
                        SUM(s.score) as total_score, AVG(s.time_taken) as avg_time
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE u.username = %s 
                    GROUP BY s.specialty
                    ORDER BY avg_score DESC
                """, (username,))
                
                specialty_data = cur.fetchall()
                
                # Progression dans le temps - REQUÊTE CORRIGÉE
                cur.execute("""
                    SELECT DATE(s.created_at) as date, AVG(s.score) as daily_avg,
                        COUNT(*) as daily_quizzes
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE u.username = %s 
                    GROUP BY DATE(s.created_at)
                    ORDER BY date
                """, (username,))
                
                timeline_data = cur.fetchall()
                
                return {
                    'by_specialty': specialty_data,
                    'timeline': timeline_data
                }
                
        except Exception as e:
            print(f"Erreur analytics: {e}")
            return None
        finally:
            conn.close()
    def debug_user_stats(self, username: str):
        """Méthode de debug pour les statistiques utilisateur"""
        conn = self.get_connection()
        if conn is None:
            return "❌ Pas de connexion"
        
        try:
            with conn.cursor() as cur:
                # Vérifier si l'utilisateur existe
                cur.execute("SELECT id, username, created_at FROM users WHERE username = %s", (username,))
                user = cur.fetchone()
                if not user:
                    return f"❌ Utilisateur {username} non trouvé"
                
                user_id = user[0]
                print(f"✅ Utilisateur trouvé: {user[1]} (ID: {user_id})")
                
                # Compter les scores
                cur.execute("SELECT COUNT(*), MAX(created_at) FROM scores WHERE user_id = %s", (user_id,))
                score_stats = cur.fetchone()
                print(f"📊 Scores: {score_stats[0]} entrées, dernière le {score_stats[1]}")
                
                # Compter les simulations ECN
                cur.execute("SELECT COUNT(*), MAX(created_at) FROM ecn_simulations WHERE user_id = %s", (user_id,))
                ecn_stats = cur.fetchone()
                print(f"🎯 Simulations ECN: {ecn_stats[0]} entrées, dernière le {ecn_stats[1]}")
                
                return "✅ Diagnostic terminé"
                
        except Exception as e:
            return f"❌ Erreur diagnostic: {e}"
        finally:
            conn.close()
            
    def save_clinical_case_score(self, username: str, specialty: str, case_title: str, score: float, total_steps: int, correct_steps: int):
        """Sauvegarde le score d'un dossier clinique"""
        conn = self.get_connection()
        if conn is None:
            return False
        
        try:
            with conn.cursor() as cur:
                # Récupérer l'ID utilisateur
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                if result:
                    user_id = result[0]
                    
                    # Sauvegarder le score (utilisation de la table scores existante)
                    cur.execute(
                        "INSERT INTO scores (user_id, specialty, score, total_questions, time_taken, case_title) VALUES (%s, %s, %s, %s, %s, %s)",
                        (user_id, specialty, int(score), total_steps, 0, case_title)  # time_taken à 0 pour les dossiers
                    )
                    
                    conn.commit()
                    return True
            return False
            
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du dossier clinique: {e}")
            return False
        finally:
            conn.close()
            
    def save_ecn_simulation(self, username: str, simulation_data: Dict):
        """Sauvegarde les résultats d'une simulation ECN - VERSION CORRIGÉE"""
        conn = self.get_connection()
        if conn is None:
            return False
        
        try:
            with conn.cursor() as cur:
                # Utiliser get_or_create_user au lieu de SELECT simple
                user_id = self.get_or_create_user(username)
                
                if not user_id:
                    print(f"❌ Impossible de créer/récupérer l'utilisateur {username}")
                    return False
                
                # Préparer les données pour l'insertion
                session = simulation_data['session']
                results = simulation_data['results']
                
                # S'assurer que simulation_data est sérialisable
                serializable_data = {
                    'session_id': session['id'],
                    'session_title': session['title'],
                    'total_questions': session['total_questions'],
                    'results_summary': {
                        'raw_score': results['raw_score'],
                        'max_score': results['max_score'],
                        'percentage': results['percentage'],
                        'passed': results['passed'],
                        'grade': results['grade']
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Sauvegarder la simulation
                cur.execute("""
                    INSERT INTO ecn_simulations 
                    (user_id, simulation_id, score, max_score, percentage, duration, passed, grade, simulation_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    session['id'],
                    float(results['raw_score']),
                    float(results['max_score']),
                    float(results['percentage']),
                    int(simulation_data.get('time_taken', 0)),
                    bool(results['passed']),
                    str(results['grade']),
                    json.dumps(serializable_data)
                ))
                
                conn.commit()
                print(f"✅ Simulation ECN sauvegardée pour {username}")
                return True
                
        except Exception as e:
            print(f"❌ Erreur sauvegarde simulation: {e}")
            import traceback
            print(f"🔍 Détails: {traceback.format_exc()}")
            return False
        finally:
            conn.close()
    
    def get_or_create_user(self, username: str, specialty: str = "general"):
        """Récupère ou crée un utilisateur - VERSION CORRIGÉE"""
        conn = self.get_connection()
        if conn is None:
            return None
        
        try:
            with conn.cursor() as cur:
                # Essayer de récupérer l'utilisateur
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                
                if result:
                    return result[0]  # Retourner l'ID existant
                else:
                    # Créer un nouvel utilisateur
                    email = f"{username}@ecn-prep.fr"
                    cur.execute(
                        "INSERT INTO users (username, email, specialty) VALUES (%s, %s, %s) RETURNING id",
                        (username, email, specialty)
                    )
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    print(f"✅ Nouvel utilisateur créé: {username} (ID: {user_id})")
                    return user_id
                    
        except Exception as e:
            print(f"❌ Erreur get_or_create_user: {e}")
            return None
        finally:
            conn.close()

    def get_ecn_leaderboard(self, limit: int = 20):
        """Récupère le classement des simulations ECN - VERSION CORRIGÉE"""
        conn = self.get_connection()
        if conn is None:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        u.username,
                        CAST(AVG(e.percentage) AS DECIMAL(5,2)) as avg_score,
                        CAST(MAX(e.percentage) AS DECIMAL(5,2)) as best_score,
                        COUNT(e.id) as simulations_count,
                        MIN(e.created_at) as first_simulation,
                        MAX(e.created_at) as last_simulation
                    FROM ecn_simulations e
                    JOIN users u ON e.user_id = u.id
                    GROUP BY u.id, u.username
                    HAVING COUNT(e.id) >= 1
                    ORDER BY best_score DESC, avg_score DESC
                    LIMIT %s
                """, (limit,))
                
                leaderboard = []
                for row in cur.fetchall():
                    leaderboard.append({
                        'username': row['username'],
                        'avg_score': float(row['avg_score']) if row['avg_score'] else 0.0,
                        'best_score': float(row['best_score']) if row['best_score'] else 0.0,
                        'simulations_count': int(row['simulations_count']),
                        'first_simulation': row['first_simulation'],
                        'last_simulation': row['last_simulation']
                    })
                
                return leaderboard
                
        except Exception as e:
            print(f"❌ Erreur classement ECN: {e}")
            import traceback
            print(f"🔍 Détails: {traceback.format_exc()}")
            return []
        finally:
            conn.close()

    def get_user_ecn_stats(self, username: str):
        """Récupère les statistiques ECN d'un utilisateur - VERSION CORRIGÉE"""
        conn = self.get_connection()
        if conn is None:
            return {}
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # D'abord s'assurer que l'utilisateur existe
                user_id = self.get_or_create_user(username)
                if not user_id:
                    return {}
                
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_simulations,
                        CAST(AVG(e.percentage) AS DECIMAL(5,2)) as average_score,
                        CAST(MAX(e.percentage) AS DECIMAL(5,2)) as best_score,
                        CAST(MIN(e.percentage) AS DECIMAL(5,2)) as worst_score,
                        CAST(AVG(e.duration) AS INTEGER) as average_time,
                        SUM(CASE WHEN e.passed = true THEN 1 ELSE 0 END) as passed_count,
                        MIN(e.created_at) as first_simulation,
                        MAX(e.created_at) as last_simulation
                    FROM ecn_simulations e
                    WHERE e.user_id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    stats = dict(result)
                    # Convertir les types pour éviter les problèmes
                    stats['total_simulations'] = int(stats['total_simulations']) if stats['total_simulations'] else 0
                    stats['passed_count'] = int(stats['passed_count']) if stats['passed_count'] else 0
                    return stats
                return {}
                
        except Exception as e:
            print(f"❌ Erreur stats ECN: {e}")
            import traceback
            print(f"🔍 Détails: {traceback.format_exc()}")
            return {}
        finally:
            conn.close()
    
    def test_connection(self):
        """Teste la connexion à Neon"""
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()
                    st.success(f"✅ Connecté à Neon: {version[0]}")
                    return True
            except Exception as e:
                st.error(f"❌ Erreur test connexion: {e}")
                return False
            finally:
                conn.close()
        return False