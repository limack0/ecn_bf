import psycopg2
from config import DatabaseConfig
import streamlit as st

def setup_database():
    """Script d'initialisation de la base de données"""
    config = DatabaseConfig()
    
    try:
        # Connexion à la base postgres par défaut pour créer la base
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database="ecn_prep",
            user=config.user,
            password=config.password
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Créer la base de données si elle n'existe pas
            cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{config.database}'")
            exists = cur.fetchone()
            
            if not exists:
                cur.execute(f"CREATE DATABASE {config.database}")
                print(f"Base de données '{config.database}' créée avec succès")
            else:
                print(f"Base de données '{config.database}' existe déjà")
        
        conn.close()
        
        # Initialiser les tables
        from database import DatabaseManager
        db = DatabaseManager()
        if db.init_database():
            print("Tables créées avec succès")
        else:
            print("Erreur lors de la création des tables")
            
    except Exception as e:
        print(f"Erreur lors du setup: {e}")

if __name__ == "__main__":
    setup_database()