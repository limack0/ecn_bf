from config import BadgeSystem
from database import DatabaseManager
from typing import Dict

class BadgeManager:
    def __init__(self):
        self.badge_system = BadgeSystem()
        self.db = DatabaseManager()
    
    def check_and_award_badges(self, username: str, new_score: int):
        """Vérifie et attribue les badges basés sur le score total"""
        conn = self.db.get_connection()
        if conn is None:
            return []
        
        try:
            with conn.cursor() as cur:
                # Récupérer le score total de l'utilisateur
                cur.execute("""
                    SELECT SUM(score) as total_score 
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE u.username = %s
                """, (username,))
                
                result = cur.fetchone()
                total_score = result[0] if result[0] else 0
                
                # Vérifier les badges existants
                cur.execute("""
                    SELECT badge_type FROM badges b
                    JOIN users u ON b.user_id = u.id
                    WHERE u.username = %s
                """, (username,))
                
                existing_badges = [row[0] for row in cur.fetchall()]
                
                # Attribuer de nouveaux badges
                new_badges = []
                for badge_id, badge_info in self.badge_system.BADGES.items():
                    if badge_id not in existing_badges and total_score >= badge_info['threshold']:
                        # Récupérer l'ID utilisateur
                        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                        user_id = cur.fetchone()[0]
                        
                        # Attribuer le badge
                        cur.execute(
                            "INSERT INTO badges (user_id, badge_type) VALUES (%s, %s)",
                            (user_id, badge_id)
                        )
                        new_badges.append(badge_info['name'])
                
                conn.commit()
                return new_badges
                
        except Exception as e:
            print(f"Erreur lors de l'attribution des badges: {e}")
            return []
        finally:
            conn.close()
    
    def get_user_badges(self, username: str):
        """Récupère les badges d'un utilisateur - VERSION CORRIGÉE"""
        conn = self.db.get_connection()
        if conn is None:
            return []
        
        try:
            with conn.cursor() as cur:
                # Récupérer les badges de l'utilisateur
                cur.execute("""
                    SELECT b.badge_type 
                    FROM badges b
                    JOIN users u ON b.user_id = u.id
                    WHERE u.username = %s
                """, (username,))
                
                user_badges = [row[0] for row in cur.fetchall()]
                
                # Convertir les IDs de badges en noms
                badge_names = []
                for badge_id in user_badges:
                    if badge_id in self.badge_system.BADGES:
                        badge_names.append(self.badge_system.BADGES[badge_id]['name'])
                
                return badge_names
                
        except Exception as e:
            print(f"Erreur lors de la récupération des badges: {e}")
            return []
        finally:
            conn.close()
            
    def check_ecn_badges(self, username: str, simulation_data: Dict):
        """Vérifie les badges spécifiques aux simulations ECN - VERSION CORRIGÉE"""
        conn = self.db.get_connection()
        if conn is None:
            return []
        
        try:
            with conn.cursor() as cur:
                # Récupérer l'ID utilisateur
                user_id = self.db.get_or_create_user(username)
                if not user_id:
                    return []
                
                # Récupérer les stats ECN de l'utilisateur
                cur.execute("""
                    SELECT COUNT(*) as total_simulations, 
                        MAX(percentage) as best_score, 
                        AVG(percentage) as avg_score
                    FROM ecn_simulations 
                    WHERE user_id = %s
                """, (user_id,))
                
                stats_result = cur.fetchone()
                if not stats_result:
                    return []
                
                total_simulations, best_score, avg_score = stats_result
                
                # Vérifier les badges existants
                cur.execute("SELECT badge_type FROM badges WHERE user_id = %s", (user_id,))
                existing_badges = [row[0] for row in cur.fetchall()]
                
                # Badges à vérifier
                badges_to_award = []
                
                # Badge simulateur (première simulation)
                if total_simulations >= 1 and "simulateur" not in existing_badges:
                    badges_to_award.append("simulateur")
                
                # Badge marathonien (5 simulations)
                if total_simulations >= 5 and "marathonien" not in existing_badges:
                    badges_to_award.append("marathonien")
                
                # Badge excellent (score ≥ 85%)
                if best_score and best_score >= 85 and "excellent" not in existing_badges:
                    badges_to_award.append("excellent")
                
                # Badge podium (dans le top 3) - vérification séparée
                cur.execute("""
                    SELECT u.username
                    FROM (
                        SELECT user_id, MAX(percentage) as best_score
                        FROM ecn_simulations
                        GROUP BY user_id
                        ORDER BY best_score DESC
                        LIMIT 3
                    ) top3
                    JOIN users u ON top3.user_id = u.id
                    WHERE u.id = %s
                """, (user_id,))
                
                if cur.fetchone() and "podium" not in existing_badges:
                    badges_to_award.append("podium")
                
                # Attribuer les nouveaux badges
                new_badges = []
                for badge_id in badges_to_award:
                    cur.execute(
                        "INSERT INTO badges (user_id, badge_type) VALUES (%s, %s)",
                        (user_id, badge_id)
                    )
                    new_badges.append(self.badge_system.BADGES[badge_id]['name'])
                
                conn.commit()
                return new_badges
                
        except Exception as e:
            print(f"❌ Erreur badges ECN: {e}")
            import traceback
            print(f"🔍 Détails: {traceback.format_exc()}")
            return []
        finally:
            conn.close()