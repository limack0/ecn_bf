from database import DatabaseManager
import streamlit as st

def test_all_fixes():
    """Teste toutes les corrections"""
    db = DatabaseManager()
    
    st.title("🧪 Test des Corrections SQL")
    
    # Test utilisateur
    test_user = "test_user"
    user_id = db.get_or_create_user(test_user)
    st.write(f"✅ Utilisateur de test créé: {test_user} (ID: {user_id})")
    
    # Test statistiques
    stats = db.get_user_ecn_stats(test_user)
    st.write(f"📊 Stats ECN: {stats}")
    
    # Test classement
    leaderboard = db.get_ecn_leaderboard(5)
    st.write(f"🏅 Classement ECN: {len(leaderboard)} entrées")
    
    # Test diagnostic
    debug_info = db.debug_user_stats(test_user)
    st.write(f"🔍 Diagnostic: {debug_info}")
    
    # Nettoyage
    conn = db.get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE username = %s", (test_user,))
    conn.commit()
    st.write("🧹 Utilisateur test nettoyé")

if __name__ == "__main__":
    test_all_fixes()