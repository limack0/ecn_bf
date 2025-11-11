from database import DatabaseManager

def fix_ambiguous_columns():
    """Corrige les problèmes de colonnes ambiguës dans la base"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    if conn:
        try:
            with conn.cursor() as cur:
                # Vérifier la structure des tables
                print("🔍 Vérification de la structure des tables...")
                
                # Table users
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
                user_columns = [row[0] for row in cur.fetchall()]
                print(f"📋 Table users: {user_columns}")
                
                # Table scores
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='scores'")
                score_columns = [row[0] for row in cur.fetchall()]
                print(f"📋 Table scores: {score_columns}")
                
                # Table ecn_simulations
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ecn_simulations'")
                ecn_columns = [row[0] for row in cur.fetchall()]
                print(f"📋 Table ecn_simulations: {ecn_columns}")
                
                # Table badges
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='badges'")
                badge_columns = [row[0] for row in cur.fetchall()]
                print(f"📋 Table badges: {badge_columns}")
                
                print("✅ Structure des tables vérifiée")
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    fix_ambiguous_columns()