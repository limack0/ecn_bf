from database import DatabaseManager

def init_neon_database():
    """Initialise la base de données Neon"""
    db = DatabaseManager()
    
    if db.test_connection():
        print("✅ Connexion Neon établie")
        if db.init_database():
            print("✅ Tables créées avec succès")
        else:
            print("❌ Erreur création tables")
    else:
        print("❌ Impossible de se connecter à Neon")

if __name__ == "__main__":
    init_neon_database()