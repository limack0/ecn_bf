import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database import DatabaseManager
import streamlit as st


class Analytics:
    def __init__(self):
        self.db = DatabaseManager()

    def get_user_progress_data(self, username: str):
        """Récupère les données de progression d'un utilisateur"""
        conn = self.db.get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                # ✅ Scores par spécialité (préfixes ajoutés)
                cur.execute("""
                    SELECT s.specialty, 
                           AVG(s.score::float) AS avg_score,
                           COUNT(*) AS quiz_count,
                           SUM(s.score) AS total_score,
                           AVG(s.time_taken) AS avg_time
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE u.username = %s 
                    GROUP BY s.specialty
                    ORDER BY avg_score DESC
                """, (username,))
                specialty_data = cur.fetchall()

                # ✅ Progression dans le temps (préfixes ajoutés)
                cur.execute("""
                    SELECT DATE(s.created_at) AS date,
                           AVG(s.score::float) AS daily_avg,
                           COUNT(*) AS daily_quizzes
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
            st.error(f"Erreur analytics: {e}")
            return None
        finally:
            conn.close()

    def create_specialty_radar_chart(self, username: str):
        """Crée un graphique radar des performances par spécialité"""
        data = self.get_user_progress_data(username)
        if not data or not data['by_specialty']:
            return None

        specialties = [row[0] for row in data['by_specialty']]
        scores = [row[1] for row in data['by_specialty']]

        fig = go.Figure(data=go.Scatterpolar(
            r=scores + [scores[0]],  # Fermer le cercle
            theta=specialties + [specialties[0]],
            fill='toself',
            name='Score moyen'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title="Performances par spécialité"
        )

        return fig

    def create_progress_timeline(self, username: str):
        """Crée un graphique de progression temporelle"""
        data = self.get_user_progress_data(username)
        if not data or not data['timeline']:
            return None

        dates = [row[0] for row in data['timeline']]
        scores = [row[1] for row in data['timeline']]

        fig = px.line(
            x=dates, y=scores,
            title="Progression des scores dans le temps",
            labels={'x': 'Date', 'y': 'Score moyen'}
        )

        fig.update_traces(mode='lines+markers')

        return fig
