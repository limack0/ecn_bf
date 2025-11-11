from database import DatabaseManager

def fix_database_issues():
    """Corrige les problèmes de base de données"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    if conn:
        try:
            with conn.cursor() as cur:
                # Vérifier et corriger la table badges si nécessaire
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='badges' AND column_name='badge_type'
                """)
                if not cur.fetchone():
                    print("Table badges nécessite une mise à jour...")
                    # Recréer la table badges
                    cur.execute("DROP TABLE IF EXISTS badges CASCADE")
                    cur.execute("""
                        CREATE TABLE badges (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id),
                            badge_type VARCHAR(100) NOT NULL,
                            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("Table badges recréée")
                
                # Vérifier la table ecn_simulations
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='ecn_simulations'
                """)
                if not cur.fetchall():
                    print("Création de la table ecn_simulations...")
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
                    print("Table ecn_simulations créée")
                
                conn.commit()
                print("✅ Base de données corrigée avec succès")
                
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    fix_database_issues()