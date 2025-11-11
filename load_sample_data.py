import json
import os
from database import DatabaseManager
import streamlit as st

def load_sample_data():
    """Charge des données d'exemple dans la base"""
    db = DatabaseManager()
    
    # Données utilisateurs exemple
    sample_users = [
        {"username": "caroline_med", "email": "caroline@ecn.fr", "specialty": "cardiologie"},
        {"username": "thomas_intern", "email": "thomas@ecn.fr", "specialty": "neurologie"},
        {"username": "sophie_resident", "email": "sophie@ecn.fr", "specialty": "pneumologie"},
    ]
    
    conn = db.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Ajouter des utilisateurs exemple
                for user in sample_users:
                    cur.execute(
                        "INSERT INTO users (username, email, specialty) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
                        (user["username"], user["email"], user["specialty"])
                    )
                
                # Ajouter des scores exemple
                sample_scores = [
                    ("caroline_med", "cardiologie", 85, 10, 300),
                    ("thomas_intern", "neurologie", 72, 10, 350),
                    ("sophie_resident", "pneumologie", 91, 10, 280),
                    ("caroline_med", "cardiologie", 78, 15, 450),
                ]
                
                for score in sample_scores:
                    cur.execute(
                        "INSERT INTO scores (user_id, specialty, score, total_questions, time_taken) SELECT id, %s, %s, %s, %s FROM users WHERE username = %s",
                        (score[1], score[2], score[3], score[4], score[0])
                    )
                
                conn.commit()
                print("Données exemple chargées avec succès")
                
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    load_sample_data()