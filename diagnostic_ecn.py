from database import DatabaseManager
import streamlit as st

def diagnostic_ecn_system():
    """Diagnostique et répare le système ECN"""
    db = DatabaseManager()
    
    st.title("🔧 Diagnostic du Système ECN")
    
    # Vérifier la connexion à la base
    conn = db.get_connection()
    if not conn:
        st.error("❌ Impossible de se connecter à la base de données")
        return
    
    st.success("✅ Connexion à la base de données établie")
    
    # Vérifier les tables
    with conn.cursor() as cur:
        # Vérifier la table users
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        st.write(f"👥 Nombre d'utilisateurs: {user_count}")
        
        # Vérifier la table ecn_simulations
        cur.execute("""
            SELECT COUNT(*) as sim_count, 
                   COUNT(DISTINCT user_id) as users_with_sims,
                   AVG(percentage) as avg_score
            FROM ecn_simulations
        """)
        sim_stats = cur.fetchone()
        st.write(f"📊 Simulations ECN: {sim_stats[0]}")
        st.write(f"👤 Utilisateurs avec simulations: {sim_stats[1]}")
        st.write(f"🎯 Score moyen: {sim_stats[2]:.1f}%" if sim_stats[2] else "🎯 Score moyen: N/A")
    
    # Test de création d'utilisateur
    test_username = "test_user_ecn"
    user_id = db.get_or_create_user(test_username)
    if user_id:
        st.success(f"✅ Test création utilisateur réussi: {test_username} (ID: {user_id})")
        
        # Nettoyer le test
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE username = %s", (test_username,))
        conn.commit()
    else:
        st.error("❌ Test création utilisateur échoué")
    
    conn.close()

if __name__ == "__main__":
    diagnostic_ecn_system()