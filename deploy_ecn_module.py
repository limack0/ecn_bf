from database import DatabaseManager
from utils.ecn_simulator import ECNSimulator
from utils.quiz_manager import QuizManager
import streamlit as st

def deploy_ecn_module():
    """Déploie le module ECN complètement"""
    
    # Initialiser la base de données
    db = DatabaseManager()
    if db.init_database():
        print("✅ Base de données ECN initialisée")
    else:
        print("❌ Erreur base de données")
        return
    
    # Vérifier les données
    quiz_mgr = QuizManager()
    specialties = quiz_mgr.get_specialties()
    
    if len(specialties) >= 5:
        print(f"✅ {len(specialties)} spécialités chargées")
        
        # Tester le simulateur
        simulator = ECNSimulator(quiz_mgr)
        test_session = simulator.generate_simulation_session()
        
        if test_session and len(test_session['questions']) == 120:
            print("✅ Simulateur ECN opérationnel")
            print("🎉 Module ECN déployé avec succès!")
        else:
            print("❌ Erreur génération simulation")
    else:
        print("❌ Données insuffisantes - chargez plus de spécialités")

if __name__ == "__main__":
    deploy_ecn_module()