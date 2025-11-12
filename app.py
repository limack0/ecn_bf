import streamlit as st
import json
import time
from database import DatabaseManager
from utils.quiz_manager import QuizManager
from utils.badge_system import BadgeManager
from config import AppConfig
from utils.analytics import Analytics

# Configuration de la page
st.set_page_config(
    page_title="ECN Prep - Plateforme de Préparation aux ECN",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
# INITIALISATION COMPLÈTE DU SESSION STATE
def initialize_session_state():
    """Initialise toutes les variables du session state"""
    defaults = {
        # Variables générales
        'username': "",
        'user_answers': [],
        'current_question': 0,
        
        # Mode Quiz
        'quiz_started': False,
        'quiz_finished': False,
        'questions': [],
        'start_time': 0,
        'end_time': 0,
        
        # Dossiers cliniques
        'clinical_case': None,
        'current_step': 0,
        'case_answers': [],
        'case_finished': False,
        'case_results': None,
        'score_saved': False,
        'show_ecn_details': False,
        
        # Mode Compétition
        'competition_mode': False,
        'comp_questions': [],
        'comp_current_q': 0,
        'comp_score': 0,
        'comp_start_time': 0,
        'comp_answered': [],
        'comp_finished': False,
        
        # Simulations ECN
        'ecn_simulator': None,
        'ecn_session': None,
        'ecn_current_section': 0,
        'ecn_current_question': 0,
        'ecn_answers': [],
        'ecn_start_time': 0,
        'ecn_end_time': 0,
        'ecn_simulation_active': False,
        'ecn_simulation_finished': False,
        'ecn_results': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialiser le session state
initialize_session_state()



# Initialisation
@st.cache_resource
def init_managers():
    db = DatabaseManager()
    db.init_database()
    quiz_mgr = QuizManager()
    badge_mgr = BadgeManager()
    return db, quiz_mgr, badge_mgr

db, quiz_mgr, badge_mgr = init_managers()
config = AppConfig()

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 0.75em;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.375rem;
        background-color: #6c757d;
        color: white;
        margin: 0.1rem;
    }
    .badge-gold { background-color: #ffd700; color: black; }
    .badge-silver { background-color: #c0c0c0; color: black; }
    .badge-bronze { background-color: #cd7f32; color: white; }
    .quiz-question {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🏥 ECN Prep")
st.sidebar.markdown("### Navigation")

menu_options = [
    "Accueil",
    "Mode Quiz", 
    "Dossiers Cliniques Progressifs",
    "Mode Compétition",
    "🏆 Simulations ECN",
    "Classement",
    "Bibliothèque de Ressources",
    "Profil et Badges"
]

choice = st.sidebar.selectbox("Choisir une section", menu_options)

def keep_alive(self):
    """Maintient la base Neon active"""
    conn = self.get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except:
            pass
        finally:
            conn.close()




# Page d'accueil
if choice == "Accueil":
    st.markdown('<div class="main-header">🏥 ECN Prep - Plateforme de Préparation</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Bienvenue sur la plateforme de préparation aux ECN
        
        Cette application vous permet de:
        
        📚 **Réviser par spécialités médicales**
        - Cardiologie, Pneumologie, Neurologie, etc.
        - Questions à choix multiples
        - Dossiers cliniques progressifs
        
        🏆 **Vous mesurer aux autres**
        - Mode compétition chronométré
        - Classement en temps réel
        - Système de badges et récompenses
        
        💼 **Travailler les dossiers cliniques**
        - Cas progressifs avec révélations successives
        - Approche par compétences
        - Feedback immédiat
        
        ### Commencez par:
        1. Créer votre profil étudiant
        2. Choisir une spécialité
        3. Démarrer un quiz ou un dossier clinique
        """)
    
    with col2:
        st.session_state.username = st.text_input("👤 Votre nom d'utilisateur", placeholder="ex: etudiant_123")
        
        if st.session_state.username:
            st.success(f"Connecté en tant que: {st.session_state.username}")
            
            # Afficher les badges de l'utilisateur
            user_badges = badge_mgr.get_user_badges(st.session_state.username)
            if user_badges:
                st.markdown("### Vos badges")
                for badge in user_badges:
                    st.markdown(f'<span class="badge badge-gold">{badge}</span>', unsafe_allow_html=True)
        
        st.markdown("### Statistiques rapides")
        specialties = quiz_mgr.get_specialties()
        if specialties:
            st.info(f"**{len(specialties)}** spécialités disponibles")
            st.info(f"**{sum(len(quiz_mgr.quizzes.get(spec, [])) for spec in specialties)}** questions au total")
        else:
            st.warning("Aucune donnée chargée. Placez vos fichiers JSON dans le dossier 'data/'")

# Mode Quiz
# Mode Quiz - VERSION ROBUSTE
elif choice == "Mode Quiz":
    st.markdown("## 📝 Mode Quiz")
    
    if not st.session_state.username:
        st.warning("Veuillez entrer votre nom d'utilisateur dans la page d'accueil")
        st.stop()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        specialty = st.selectbox("Choisir une spécialité", quiz_mgr.get_specialties())
        num_questions = st.slider("Nombre de questions", 5, 20, 10)
        
        if st.button("🚀 Démarrer le Quiz", key= "ecn_start_quiz") and not st.session_state.quiz_started:
            questions = quiz_mgr.get_quiz_questions(specialty, num_questions)
            if questions:
                st.session_state.questions = questions
                st.session_state.user_answers = [{} for _ in range(len(questions))]
                st.session_state.current_question = 0
                st.session_state.quiz_started = True
                st.session_state.quiz_finished = False
                st.session_state.start_time = time.time()
                st.session_state.end_time = 0
                st.rerun()
            else:
                st.error("Aucune question disponible pour cette spécialité")
    
    with col2:
        if st.session_state.quiz_started and not st.session_state.quiz_finished:
            current_q = st.session_state.current_question
            total_q = len(st.session_state.questions)
            st.info(f"Question {current_q + 1}/{total_q}")
            progress = (current_q) / total_q
            st.progress(progress)
            
            if st.button("⏹️ Arrêter le quiz"):
                st.session_state.quiz_finished = True
                st.session_state.end_time = time.time()
                st.rerun()
    
    # Affichage des questions - AVEC VÉRIFICATIONS
    if (st.session_state.quiz_started and 
        not st.session_state.quiz_finished and 
        st.session_state.questions):
        
        current_idx = st.session_state.current_question
        questions = st.session_state.questions
        
        # Vérification de sécurité de l'index
        if current_idx < len(questions):
            question = questions[current_idx]
            
            st.markdown(f'<div class="quiz-question"><h3>Question {current_idx + 1}</h3><p>{question["question"]}</p></div>', unsafe_allow_html=True)
            
            if question['type'] == 'single':
                options = [opt['text'] for opt in question['options']]
                selected = st.radio("Choisissez votre réponse:", options, key=f"q{current_idx}")
                st.session_state.user_answers[current_idx] = {'selected': selected}
                
            elif question['type'] == 'multiple':
                options = [opt['text'] for opt in question['options']]
                selected = st.multiselect("Choisissez une ou plusieurs réponses:", options, key=f"q{current_idx}")
                st.session_state.user_answers[current_idx] = {'selected': selected}
            
            col_prev, col_next = st.columns([1, 1])
            with col_prev:
                if current_idx > 0:
                    if st.button("⬅️ Question précédente"):
                        st.session_state.current_question -= 1
                        st.rerun()
            
            with col_next:
                if current_idx < len(questions) - 1:
                    if st.button("Question suivante ➡️"):
                        st.session_state.current_question += 1
                        st.rerun()
                else:
                    if st.button("✅ Terminer le quiz"):
                        st.session_state.quiz_finished = True
                        st.session_state.end_time = time.time()  # INITIALISATION
                        st.rerun()
        else:
            st.error("Erreur: index de question invalide")
            st.session_state.quiz_finished = True
            st.rerun()
    
    # RÉSULTATS DU QUIZ - VERSION ROBUSTE
    elif st.session_state.quiz_finished:
        # Calcul du temps avec valeurs par défaut
        start_time = getattr(st.session_state, 'start_time', time.time())
        end_time = getattr(st.session_state, 'end_time', time.time())
        time_taken = int(end_time - start_time)
        
        # Calcul du score avec vérifications
        if (hasattr(st.session_state, 'questions') and 
            hasattr(st.session_state, 'user_answers') and 
            st.session_state.questions):
            
            score = quiz_mgr.calculate_score(st.session_state.user_answers, st.session_state.questions)
            total_questions = len(st.session_state.questions)
            
            st.success(f"🎉 Quiz terminé! Score: {score}/{total_questions}")
            st.info(f"⏱️ Temps: {time_taken} secondes")
            
            # Sauvegarde du score
            if db.save_score(st.session_state.username, specialty, score, total_questions, time_taken):
                st.success("Score sauvegardé!")
                
                # Vérification des badges
                new_badges = badge_mgr.check_and_award_badges(st.session_state.username, score)
                if new_badges:
                    st.balloons()
                    st.success("🎖️ Nouveaux badges débloqués!")
                    for badge in new_badges:
                        st.markdown(f'<span class="badge badge-gold">{badge}</span>', unsafe_allow_html=True)
        else:
            st.error("Erreur: impossible de calculer le score")
            score = 0
            total_questions = 0
        
        # Réinitialisation
        if st.button("🔄 Nouveau quiz"):
            # Réinitialiser uniquement les variables du quiz
            st.session_state.quiz_started = False
            st.session_state.quiz_finished = False
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            st.session_state.questions = []
            st.session_state.start_time = 0
            st.session_state.end_time = 0
            st.rerun()

# Dossiers Cliniques Progressifs
# Dossiers Cliniques Progressifs
elif choice == "Dossiers Cliniques Progressifs":
    st.markdown("## 💼 Dossiers Cliniques Progressifs")
    
    if not st.session_state.username:
        st.warning("Veuillez entrer votre nom d'utilisateur dans la page d'accueil")
        st.stop()
    
    specialty = st.selectbox("Choisir une spécialité", quiz_mgr.get_specialties(), key="clinical_specialty")
    
    if st.button("📂 Charger un nouveau dossier clinique"):
        clinical_case = quiz_mgr.get_progressive_clinical_case(specialty)
        if clinical_case:
            st.session_state.clinical_case = clinical_case
            st.session_state.current_step = 0
            st.session_state.case_answers = []
            st.session_state.case_finished = False
            st.session_state.case_results = None
            st.session_state.score_saved = False
        else:
            st.error("Aucun dossier clinique disponible pour cette spécialité")
    
    if 'clinical_case' in st.session_state and not st.session_state.get('case_finished', False):
        if 'clinical_case' not in st.session_state or st.session_state.clinical_case is None:
            st.warning("Aucun dossier clinique chargé. Cliquez sur '📂 Charger un nouveau dossier clinique'.")
            st.stop()
        case = st.session_state.clinical_case
        current_step = st.session_state.current_step
        
        st.markdown(f"### {case['title']}")
        st.markdown(f"**Difficulté:** {case.get('difficulty', 'Non spécifiée')}")
        
        # Barre de progression
        total_steps = len(case['steps'])
        progress = current_step / total_steps
        st.progress(progress)
        st.write(f"Étape {current_step + 1} sur {total_steps}")
        
        # Affichage progressif
        if current_step < len(case['steps']):
            step = case['steps'][current_step]
            
            st.markdown(f"#### {step['title']}")
            st.markdown(step['content'])
            
            # Initialiser la réponse si elle n'existe pas encore
            current_answer_exists = any(ans['step'] == current_step for ans in st.session_state.case_answers)
            
            if 'question' in step:
                st.markdown("---")
                st.markdown(f"**❓ Question:** {step['question']}")
                
                if step.get('type') == 'multiple_choice':
                    options = step['options']
                    default_index = 0
                    if current_answer_exists:
                        existing_answer = next(ans for ans in st.session_state.case_answers if ans['step'] == current_step)
                        if existing_answer['answer'] in options:
                            default_index = options.index(existing_answer['answer'])
                    
                    answer = st.radio("Choisissez votre réponse:", options, key=f"step_{current_step}", index=default_index)
                
                elif step.get('type') == 'multiple':
                    options = step['options']
                    default_selection = []
                    if current_answer_exists:
                        existing_answer = next(ans for ans in st.session_state.case_answers if ans['step'] == current_step)
                        default_selection = existing_answer['answer'] if isinstance(existing_answer['answer'], list) else [existing_answer['answer']]
                    
                    answer = st.multiselect("Sélectionnez une ou plusieurs réponses:", options, key=f"step_{current_step}", default=default_selection)
                
                elif step.get('type') == 'text':
                    default_text = ""
                    if current_answer_exists:
                        existing_answer = next(ans for ans in st.session_state.case_answers if ans['step'] == current_step)
                        default_text = existing_answer['answer']
                    
                    answer = st.text_area("Votre analyse:", key=f"step_{current_step}", height=150, value=default_text)
                
                else:
                    default_text = ""
                    if current_answer_exists:
                        existing_answer = next(ans for ans in st.session_state.case_answers if ans['step'] == current_step)
                        default_text = existing_answer['answer']
                    
                    answer = st.text_input("Votre réponse:", key=f"step_{current_step}", value=default_text)
            else:
                answer = None
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if current_step > 0 and st.button("⬅️ Étape précédente"):
                    # Sauvegarder la réponse actuelle avant de changer d'étape
                    if answer is not None:
                        existing_answer_index = next((i for i, ans in enumerate(st.session_state.case_answers) 
                                                   if ans['step'] == current_step), -1)
                        
                        if existing_answer_index >= 0:
                            st.session_state.case_answers[existing_answer_index]['answer'] = answer
                        else:
                            st.session_state.case_answers.append({
                                'step': current_step, 
                                'answer': answer
                            })
                    
                    st.session_state.current_step -= 1
                    st.rerun()
            
            with col2:
                if answer is not None and st.button("💾 Sauvegarder cette étape"):
                    # Sauvegarder la réponse
                    existing_answer_index = next((i for i, ans in enumerate(st.session_state.case_answers) 
                                               if ans['step'] == current_step), -1)
                    
                    if existing_answer_index >= 0:
                        st.session_state.case_answers[existing_answer_index]['answer'] = answer
                    else:
                        st.session_state.case_answers.append({
                            'step': current_step, 
                            'answer': answer
                        })
                    
                    st.success("Réponse sauvegardée!")
            
            with col3:
                if current_step < len(case['steps']) - 1:
                    if st.button("Étape suivante ➡️"):
                        # Sauvegarder la réponse actuelle avant de changer d'étape
                        if answer is not None:
                            existing_answer_index = next((i for i, ans in enumerate(st.session_state.case_answers) 
                                                       if ans['step'] == current_step), -1)
                            
                            if existing_answer_index >= 0:
                                st.session_state.case_answers[existing_answer_index]['answer'] = answer
                            else:
                                st.session_state.case_answers.append({
                                    'step': current_step, 
                                    'answer': answer
                                })
                        
                        st.session_state.current_step += 1
                        st.rerun()
                else:
                    if st.button("✅ Terminer le dossier"):
                        # Sauvegarder la dernière réponse
                        if answer is not None:
                            existing_answer_index = next((i for i, ans in enumerate(st.session_state.case_answers) 
                                                       if ans['step'] == current_step), -1)
                            
                            if existing_answer_index >= 0:
                                st.session_state.case_answers[existing_answer_index]['answer'] = answer
                            else:
                                st.session_state.case_answers.append({
                                    'step': current_step, 
                                    'answer': answer
                                })
                        
                        # Calculer les résultats
                        st.session_state.case_results = quiz_mgr.calculate_clinical_case_score(
                            case, st.session_state.case_answers
                        )
                        st.session_state.case_finished = True
                        st.rerun()
    
    # Affichage des résultats
    elif st.session_state.get('case_finished', False) and st.session_state.get('case_results'):
        case = st.session_state.clinical_case
        results = st.session_state.case_results
        
        st.markdown("## 📊 Résultats du Dossier Clinique")
        
        # Score global
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Score", f"{results['score_percentage']:.1f}%")
        with col2:
            st.metric("✅ Réponses correctes", f"{results['correct_steps']}/{results['total_steps']}")
        with col3:
            performance = "Excellent" if results['score_percentage'] >= 80 else "Bon" if results['score_percentage'] >= 60 else "À revoir"
            st.metric("🎯 Performance", performance)
        
        # Sauvegarder le score et vérifier les badges
        if not st.session_state.get('score_saved', False):
            # Sauvegarder le score
            success = db.save_clinical_case_score(
                st.session_state.username,
                specialty,
                case['title'],
                results['score_percentage'],
                results['total_steps'],
                results['correct_steps']
            )
            if success:
                st.session_state.score_saved = True
                
                # Vérifier les badges
                new_badges = badge_mgr.check_and_award_badges(st.session_state.username, int(results['score_percentage']))
                if new_badges:
                    st.balloons()
                    st.success("🎖️ Nouveaux badges débloqués!")
                    for badge in new_badges:
                        st.markdown(f'<span class="badge badge-gold">{badge}</span>', unsafe_allow_html=True)
        
        # Feedback détaillé
        st.markdown("### 📝 Détail des réponses")
        
        for feedback in results['detailed_feedback']:
            with st.expander(f"Étape {feedback['step'] + 1}: {feedback['title']}"):
                st.markdown(f"**Question:** {feedback['question']}")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("**Votre réponse:**")
                    if isinstance(feedback['user_answer'], list):
                        if feedback['user_answer']:
                            for ans in feedback['user_answer']:
                                st.write(f"- {ans}")
                        else:
                            st.write("Aucune réponse sélectionnée")
                    else:
                        st.write(feedback['user_answer'])
                
                with col_b:
                    st.markdown("**Réponse attendue:**")
                    st.write(feedback['correct_answer'])
                
                st.markdown("**Explication:**")
                st.info(feedback['explanation'])
                
                if feedback['is_correct']:
                    st.success("✅ Bonne réponse!")
                else:
                    st.error("❌ Réponse incorrecte")
        
        # Solution complète
        st.markdown("### 🎯 Solution et Discussion Complète")
        st.markdown(case.get('solution', 'Aucune solution disponible.'))
        
        # Recommandations
        st.markdown("### 📚 Points à revoir")
        if results['score_percentage'] < 60:
            st.warning("""
            **Recommandations:**
            - Revoyez les concepts fondamentaux de cette spécialité
            - Consultez les ressources de la bibliothèque
            - Entraînez-vous avec d'autres dossiers similaires
            """)
        elif results['score_percentage'] < 80:
            st.info("""
            **Recommandations:**
            - Bonne maîtrise générale
            - Travaillez les points spécifiques où vous avez fait des erreurs
            - Poursuivez votre entraînement avec des dossiers plus complexes
            """)
        else:
            st.success("""
            **Recommandations:**
            - Excellente performance!
            - Vous maîtrisez bien ce sujet
            - Passez à des dossiers de difficulté supérieure
            """)
        
        # Boutons d'action
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Nouveau dossier clinique"):
                for key in ['clinical_case', 'current_step', 'case_answers', 'case_finished', 'case_results', 'score_saved']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("🔄 Refaire le même dossier"):
                st.session_state.current_step = 0
                st.session_state.case_answers = []
                st.session_state.case_finished = False
                st.session_state.case_results = None
                st.session_state.score_saved = False
                st.rerun()

# Mode Compétition
# Mode Compétition
elif choice == "Mode Compétition":
    st.markdown("## 🏆 Mode Compétition")
    
    if not st.session_state.username:
        st.warning("Veuillez entrer votre nom d'utilisateur dans la page d'accueil")
        st.stop()
    
    st.markdown("""
    ### Défi Chronométré
    
    Dans ce mode, vous avez **10 minutes** pour répondre au maximum de questions.
    Chaque bonne réponse rapporte des points, mais les mauvaises réponses en retirent!
    
    **Règles:**
    - ⏱️ 10 minutes maximum
    - ✅ Bonne réponse: +2 points
    - ❌ Mauvaise réponse: -1 point
    - ⏭️ Passer une question: 0 point
    """)
    
    # Initialiser l'état de compétition
    if 'competition_mode' not in st.session_state:
        st.session_state.competition_mode = False
    if 'comp_questions' not in st.session_state:
        st.session_state.comp_questions = []
    if 'comp_current_q' not in st.session_state:
        st.session_state.comp_current_q = 0
    if 'comp_score' not in st.session_state:
        st.session_state.comp_score = 0
    if 'comp_start_time' not in st.session_state:
        st.session_state.comp_start_time = None
    if 'comp_answered' not in st.session_state:
        st.session_state.comp_answered = []
    
    if st.button("🎯 Démarrer la compétition", type="primary") and not st.session_state.competition_mode:
        # Générer les questions pour la compétition
        all_questions = []
        specialties = quiz_mgr.get_specialties()
        
        # Collecter des questions de toutes les spécialités
        for specialty in specialties:
            specialty_questions = quiz_mgr.get_quiz_questions(specialty, 10)  # 10 questions par spécialité
            all_questions.extend(specialty_questions)
        
        # Mélanger et sélectionner 50 questions maximum
        import random
        random.shuffle(all_questions)
        st.session_state.comp_questions = all_questions[:50]  # Maximum 50 questions
        
        # Initialiser l'état
        st.session_state.comp_current_q = 0
        st.session_state.comp_score = 0
        st.session_state.comp_start_time = time.time()
        st.session_state.comp_answered = [False] * len(st.session_state.comp_questions)
        st.session_state.competition_mode = True
        st.session_state.comp_finished = False
        st.rerun()
    
    # VÉRIFICATION DE SÉCURITÉ - S'assurer que l'index est valide
    if st.session_state.competition_mode and st.session_state.comp_questions:
        current_index = st.session_state.comp_current_q
        if current_index >= len(st.session_state.comp_questions):
            st.session_state.comp_current_q = len(st.session_state.comp_questions) - 1
            st.rerun()
    
    if st.session_state.get('competition_mode', False) and not st.session_state.get('comp_finished', False):
        # Vérifier qu'il y a des questions
        if not st.session_state.comp_questions:
            st.error("Aucune question disponible pour la compétition")
            st.session_state.competition_mode = False
            st.rerun()
        
        # Timer
        elapsed_time = time.time() - st.session_state.comp_start_time
        remaining_time = 600 - elapsed_time  # 10 minutes
        
        if remaining_time <= 0:
            st.session_state.competition_mode = False
            st.session_state.comp_finished = True
            st.error("⏰ Temps écoulé!")
            st.success(f"Score final: {st.session_state.comp_score} points")
            
            # Sauvegarde du score de compétition
            db.save_score(st.session_state.username, "competition", st.session_state.comp_score, 
                         sum(st.session_state.comp_answered), int(elapsed_time))
            
            if st.button("🔄 Rejouer"):
                st.session_state.competition_mode = False
                st.session_state.comp_finished = False
                st.rerun()
        
        else:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.metric("⏱️ Temps restant", f"{minutes:02d}:{seconds:02d}")
            with col2:
                st.metric("🎯 Score actuel", st.session_state.comp_score)
            with col3:
                st.metric("📊 Progression", f"{st.session_state.comp_current_q + 1}/{len(st.session_state.comp_questions)}")
            
            # BARRE DE PROGRESSION
            progress = (st.session_state.comp_current_q + 1) / len(st.session_state.comp_questions)
            st.progress(min(1.0, progress))
            
            # Question actuelle - AVEC VÉRIFICATION DE SÉCURITÉ
            current_index = st.session_state.comp_current_q
            if current_index < len(st.session_state.comp_questions):
                question = st.session_state.comp_questions[current_index]
                
                st.markdown(f'<div class="quiz-question"><h3>Question {current_index + 1}</h3><p>{question["question"]}</p></div>', unsafe_allow_html=True)
                
                options = [opt['text'] for opt in question['options']]
                user_answer = st.radio("Votre réponse:", options + ["⏭️ Passer"], key="comp_question")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                
                with col_btn1:
                    if st.button("✅ Valider", width='stretch') and user_answer != "⏭️ Passer":
                        correct_answers = [opt['text'] for opt in question['options'] if opt.get('correct', False)]
                        
                        if question['type'] == 'single':
                            if user_answer in correct_answers:
                                st.session_state.comp_score += 2
                                st.success("Bonne réponse! +2 points")
                            else:
                                st.session_state.comp_score = max(0, st.session_state.comp_score - 1)
                                st.error("Mauvaise réponse! -1 point")
                        
                        elif question['type'] == 'multiple':
                            user_selection = [user_answer]  # Pour single, on a une seule réponse
                            correct_count = sum(1 for ans in user_selection if ans in correct_answers)
                            incorrect_count = sum(1 for ans in user_selection if ans not in correct_answers)
                            
                            if correct_count == len(correct_answers) and incorrect_count == 0:
                                st.session_state.comp_score += 2
                                st.success("Réponse parfaite! +2 points")
                            elif correct_count > 0:
                                score_gain = max(0, (correct_count * 0.5) - (incorrect_count * 0.5))
                                st.session_state.comp_score += score_gain
                                st.info(f"Réponse partielle! +{score_gain} point(s)")
                            else:
                                st.session_state.comp_score = max(0, st.session_state.comp_score - 1)
                                st.error("Mauvaise réponse! -1 point")
                        
                        st.session_state.comp_answered[current_index] = True
                        
                        # Passer à la question suivante
                        if st.session_state.comp_current_q < len(st.session_state.comp_questions) - 1:
                            st.session_state.comp_current_q += 1
                        else:
                            st.session_state.comp_current_q = 0  # Recommencer depuis le début
                        st.rerun()
                
                with col_btn2:
                    if st.button("⏭️ Passer", width='stretch'):
                        # Passer sans pénalité
                        if st.session_state.comp_current_q < len(st.session_state.comp_questions) - 1:
                            st.session_state.comp_current_q += 1
                        else:
                            st.session_state.comp_current_q = 0  # Recommencer depuis le début
                        st.rerun()
                
                with col_btn3:
                    if st.button("🏁 Terminer", type="secondary", width='stretch'):
                        st.session_state.competition_mode = False
                        st.session_state.comp_finished = True
                        
                        # Sauvegarder le score
                        db.save_score(st.session_state.username, "competition", st.session_state.comp_score, 
                                     sum(st.session_state.comp_answered), int(elapsed_time))
                        st.rerun()
                
                # NAVIGATION RAPIDE
                st.markdown("---")
                st.markdown("**Navigation rapide:**")
                
                # Afficher les 10 prochaines questions
                start_idx = max(0, current_index - 5)
                end_idx = min(len(st.session_state.comp_questions), current_index + 6)
                
                nav_cols = st.columns(end_idx - start_idx)
                for i, col_idx in enumerate(range(start_idx, end_idx)):
                    with nav_cols[i]:
                        status = "✅" if st.session_state.comp_answered[col_idx] else "⚪"
                        is_current = "🔵" if col_idx == current_index else ""
                        if st.button(f"{status}{is_current}{col_idx + 1}", 
                                   key=f"nav_{col_idx}",
                                   width='stretch',
                                   type="primary" if col_idx == current_index else "secondary"):
                            st.session_state.comp_current_q = col_idx
                            st.rerun()
            
            else:
                # Cas où l'index est hors limites
                st.error("Erreur: index de question invalide")
                st.session_state.comp_current_q = 0
                st.rerun()
    
    # Écran de fin de compétition
    elif st.session_state.get('comp_finished', False):
        st.markdown("## 🎉 Compétition Terminée!")
        
        total_questions = len(st.session_state.comp_questions) if st.session_state.comp_questions else 0
        answered_questions = sum(st.session_state.comp_answered) if st.session_state.comp_answered else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Score Final", st.session_state.comp_score)
        with col2:
            st.metric("✅ Questions répondues", f"{answered_questions}/{total_questions}")
        with col3:
            accuracy = (st.session_state.comp_score / (answered_questions * 2)) * 100 if answered_questions > 0 else 0
            st.metric("🎯 Précision", f"{accuracy:.1f}%")
        
        # Classement instantané
        st.markdown("### 📊 Performance")
        if accuracy >= 80:
            st.success("🌟 Performance excellente! Vous maîtrisez bien les concepts.")
        elif accuracy >= 60:
            st.info("💪 Bonne performance! Continuez à vous entraîner.")
        else:
            st.warning("📚 Performance correcte. Revoyez les notions difficiles.")
        
        # Boutons d'action
        col_restart, col_home = st.columns(2)
        with col_restart:
            if st.button("🔄 Nouvelle compétition", width='stretch'):
                # Réinitialiser l'état
                for key in [k for k in st.session_state.keys() if k.startswith('comp_')]:
                    del st.session_state[key]
                st.rerun()
        
        with col_home:
            if st.button("🏠 Retour à l'accueil", width='stretch'):
                # Réinitialiser l'état
                for key in [k for k in st.session_state.keys() if k.startswith('comp_')]:
                    del st.session_state[key]
                st.rerun()

# Classement
elif choice == "Classement":
    st.markdown("## 📊 Classement")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        specialty_filter = st.selectbox("Filtrer par spécialité", ["Toutes"] + quiz_mgr.get_specialties())
        limit = st.slider("Nombre de résultats", 5, 50, 10)
    
    with col2:
        if specialty_filter == "Toutes":
            leaderboard = db.get_leaderboard(limit=limit)
        else:
            leaderboard = db.get_leaderboard(specialty=specialty_filter, limit=limit)
        
        if leaderboard:
            st.markdown("### Top Étudiants")
            
            for i, student in enumerate(leaderboard):
                col_rank, col_name, col_score, col_quizzes = st.columns([1, 3, 2, 2])
                
                with col_rank:
                    if i == 0:
                        st.markdown("🥇")
                    elif i == 1:
                        st.markdown("🥈")
                    elif i == 2:
                        st.markdown("🥉")
                    else:
                        st.markdown(f"**#{i+1}**")
                
                with col_name:
                    st.write(student['username'])
                
                with col_score:
                    st.write(f"**{student['total_score']}** pts")
                
                with col_quizzes:
                    st.write(f"{student['quizzes_taken']} quiz")
        else:
            st.info("Aucun score enregistré pour le moment")

# Bibliothèque de Ressources
elif choice == "Bibliothèque de Ressources":
    st.markdown("## 📚 Bibliothèque de Ressources")
    
    st.markdown("""
    ### Ressources par Spécialité
    
    Cette section rassemble les ressources essentielles pour votre préparation aux ECN.
    """)
    
    specialties = quiz_mgr.get_specialties()
    
    for specialty in specialties:
        with st.expander(f"📖 {specialty.capitalize()}"):
            st.markdown(f"""
            **Ressources recommandées pour la {specialty}:**
            
            📕 **Ouvrages de référence:**
            - Traité de {specialty} - Édition ECN
            - Guide pratique du clinicien
            - Cas cliniques commentés
            
            🌐 **Sites internet:**
            - Collège des Enseignants de {specialty.capitalize()}
            - Revues spécialisées
            - Banques de données médicales
            
            📱 **Applications utiles:**
            - Quiz {specialty} ECN
            - Dictionnaire Vidal
            - Calculatrices médicales
            
            **Nombre de questions disponibles:** {len(quiz_mgr.quizzes.get(specialty, []))}
            **Dossiers cliniques:** {len(quiz_mgr.clinical_cases.get(specialty, []))}
            """)

# Dans la section "Profil et Badges", ajoutez :
elif choice == "Profil et Badges":
    st.markdown("## 👤 Profil et Badges")
    
    if not st.session_state.username:
        st.warning("Veuillez entrer votre nom d'utilisateur dans la page d'accueil")
        st.stop()
    
    # Initialiser analytics
    analytics = Analytics()
    
    tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "🎖️ Badges", "📈 Progression"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Vos informations")
            st.info(f"**Utilisateur:** {st.session_state.username}")
            
            # Récupération des statistiques globales
            conn = db.get_connection()
            with conn.cursor() as cur:
                # Stats globales - REQUÊTE CORRIGÉE
                cur.execute("""
                    SELECT COUNT(*), SUM(s.score), AVG(s.score::float), 
                        MIN(s.created_at), MAX(s.created_at)
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE u.username = %s
                """, (st.session_state.username,))
                
                global_stats = cur.fetchone()
                    
                if global_stats:
                    st.metric("📚 Quiz complétés", global_stats[0])
                    st.metric("🏆 Score total", f"{global_stats[1]} pts")
                    st.metric("📈 Moyenne générale", f"{global_stats[2]:.1f}%")
                        
                    if global_stats[3]:
                        st.metric("🎯 Début", global_stats[3].strftime("%d/%m/%Y"))
        
        with col2:
            st.markdown("### Performances par spécialité")
            
            # Graphique radar
            radar_chart = analytics.create_specialty_radar_chart(st.session_state.username)
            if radar_chart:
                st.plotly_chart(radar_chart, width='stretch')
            else:
                st.info("Complétez des quiz pour voir vos statistiques")
    
    with tab2:
        st.markdown("### 🎖️ Vos badges")
        
        badges = badge_mgr.get_user_badges(st.session_state.username)
        badge_info = badge_mgr.badge_system.BADGES
        
        if badges:
            cols = st.columns(3)
            for i, badge in enumerate(badges):
                with cols[i % 3]:
                    for badge_id, info in badge_info.items():
                        if info['name'] == badge:
                            st.markdown(f"""
                            <div style='text-align: center; padding: 1rem; border: 2px solid gold; border-radius: 10px; margin: 0.5rem;'>
                                <h4>🏅</h4>
                                <h5>{badge}</h5>
                                <p>Seuil: {info['threshold']} pts</p>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Badges manquants
            st.markdown("### 🔮 Prochains badges à débloquer")
            earned_badges = badge_mgr.get_user_badges(st.session_state.username)

            missing_badges = {k: v for k, v in badge_mgr.badge_system.BADGES.items() 
                            if v['name'] not in earned_badges}
            
            if missing_badges:
                for badge_id, info in list(missing_badges.items())[:3]:
                    st.write(f"**{info['name']}** - {info['threshold']} points nécessaires")
            else:
                st.success("🎉 Félicitations ! Vous avez débloqué tous les badges !")
        else:
            st.info("Vous n'avez pas encore de badges. Complétez des quiz pour en gagner!")
    
    with tab3:
        st.markdown("### 📈 Votre progression")
        
        timeline_chart = analytics.create_progress_timeline(st.session_state.username)
        if timeline_chart:
            st.plotly_chart(timeline_chart, width='stretch')
            
            # Recommandations basées sur les données
            st.markdown("### 💡 Recommandations personnalisées")
            
            data = analytics.get_user_progress_data(st.session_state.username)
            if data and data['by_specialty']:
                weakest_specialty = min(data['by_specialty'], key=lambda x: x[1])
                strongest_specialty = max(data['by_specialty'], key=lambda x: x[1])
                
                st.warning(f"**À travailler : {weakest_specialty[0].capitalize()}** (score moyen: {weakest_specialty[1]:.1f}%)")
                st.success(f"**Points forts : {strongest_specialty[0].capitalize()}** (score moyen: {strongest_specialty[1]:.1f}%)")
        else:
            st.info("Complétez plus de quiz pour voir votre progression détaillée")


# Nouvelle section Simulations ECN
# Simulations ECN
elif choice == "🏆 Simulations ECN":
    st.markdown("## 🏆 Simulations ECN Complètes")
    
    if not st.session_state.username:
        st.warning("Veuillez entrer votre nom d'utilisateur dans la page d'accueil")
        st.stop()
    
    # Initialiser le simulateur
    if 'ecn_simulator' not in st.session_state or st.session_state.ecn_simulator is None:
        from utils.ecn_simulator import ECNSimulator
        st.session_state.ecn_simulator = ECNSimulator(quiz_mgr)
    
    simulator = st.session_state.ecn_simulator
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Nouvelle Simulation", "📊 Mes Résultats", "🏅 Classement ECN", "ℹ️ Informations"])
    
    with tab1:
        st.markdown("""
        ### Simulation ECN Complète
        
        **Caractéristiques de la simulation:**
        - ⏱️ **Durée :** 60 minutes
        - 📝 **120 questions** réparties en 4 sections
        - 🏥 **Toutes spécialités** selon la distribution réelle
        - 📊 **Barème ECN** avec pénalités pour mauvaises réponses
        - 🎯 **Score de réussite :** 70%
        
        **Déroulement:**
        1. 4 sections de 30 questions (15 minutes par section)
        2. Pause de 10 minutes à mi-parcours
        3. Timer visible en permanence
        4. Navigation libre entre les questions
        5. Validation finale avec résultats détaillés
        """)
        
        # Bouton pour démarrer une nouvelle simulation
        if st.button("🎯 Démarrer une Simulation ECN", type="primary", use_container_width=True, key="start_ecn_btn"):
            # Générer une nouvelle session
            session = simulator.generate_simulation_session()
            if session and session['questions']:
                st.session_state.ecn_session = session
                st.session_state.ecn_current_section = 0
                st.session_state.ecn_current_question = 0
                st.session_state.ecn_answers = [{} for _ in range(session['total_questions'])]
                st.session_state.ecn_start_time = time.time()
                st.session_state.ecn_simulation_active = True
                st.session_state.ecn_simulation_finished = False
                st.session_state.ecn_results = None
                st.rerun()
            else:
                st.error("❌ Impossible de générer la simulation. Vérifiez les données disponibles.")
    
        # SIMULATION ACTIVE - GESTION CORRIGÉE
        if st.session_state.get('ecn_simulation_active') and not st.session_state.get('ecn_simulation_finished'):
            session = st.session_state.ecn_session
            current_section = st.session_state.ecn_current_section
            current_question_global = st.session_state.ecn_current_question
            
            # Vérifications de sécurité
            if not session or not session.get('questions'):
                st.error("❌ Session de simulation invalide")
                st.session_state.ecn_simulation_active = False
                st.rerun()
            
            # Timer
            elapsed_time = time.time() - st.session_state.ecn_start_time
            remaining_time = max(0, session['duration'] - elapsed_time)
            
            # Gestion de la fin du temps
            if remaining_time <= 0:
                st.session_state.ecn_simulation_finished = True
                st.session_state.ecn_end_time = time.time()
                # Calculer les résultats
                time_taken = session['duration']
                results = simulator.calculate_ecn_score(st.session_state.ecn_answers, session['questions'])
                st.session_state.ecn_results = {
                    'session': session,
                    'results': results,
                    'time_taken': time_taken,
                    'user_answers': st.session_state.ecn_answers
                }
                st.rerun()
            
            # Header avec informations
            col_time, col_progress, col_section = st.columns([2, 3, 2])
            
            with col_time:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                st.metric("⏱️ Temps restant", f"{minutes:02d}:{seconds:02d}")
            
            with col_progress:
                progress = (current_question_global + 1) / len(session['questions'])
                progress_value = min(1.0, max(0.0, progress))
                st.progress(progress_value)
                st.write(f"Question {current_question_global + 1}/{len(session['questions'])}")
            
            with col_section:
                st.metric("📂 Section", f"{current_section + 1}/4")
            
            # Navigation entre sections
            st.markdown("### Navigation entre Sections")
            section_cols = st.columns(4)
            
            for i in range(4):
                with section_cols[i]:
                    section_progress = len([ans for j, ans in enumerate(st.session_state.ecn_answers) 
                                        if j // 30 == i and ans.get('selected')]) / 30
                    status = "✅" if section_progress == 1 else "🟡" if section_progress > 0 else "⚪"
                    is_current = "🔵" if i == current_section else ""
                    
                    # Utiliser un formulaire pour éviter le rechargement
                    if st.button(f"{status}{is_current}Section {i+1}", 
                            key=f"section_btn_{i}",
                            use_container_width=True,
                            type="primary" if i == current_section else "secondary"):
                        st.session_state.ecn_current_section = i
                        st.session_state.ecn_current_question = i * 30
                        st.rerun()
            
            # Question actuelle
            st.markdown("---")
            question = session['questions'][current_question_global]
            section_offset = current_question_global % 30
            
            st.markdown(f"### Section {current_section + 1} - Question {section_offset + 1}")
            st.markdown(f'<div class="quiz-question"><h4>{question["question"]}</h4></div>', unsafe_allow_html=True)
            
            # Gestion des réponses avec état préservé
            current_answer_key = f"ecn_answer_{current_question_global}"
            
            # Réponses
            if question['type'] == 'single':
                options = [opt['text'] for opt in question['options']]
                current_answer = st.session_state.ecn_answers[current_question_global].get('selected', '')
                
                # Utiliser un index pour préserver la sélection
                default_index = options.index(current_answer) if current_answer in options else 0
                selected = st.radio("Choisissez votre réponse:", 
                                options, 
                                index=default_index,
                                key=current_answer_key)
                
                # Sauvegarder immédiatement la réponse
                st.session_state.ecn_answers[current_question_global]['selected'] = selected
                
            elif question['type'] == 'multiple':
                options = [opt['text'] for opt in question['options']]
                current_answers = st.session_state.ecn_answers[current_question_global].get('selected', [])
                
                selected = st.multiselect("Choisissez une ou plusieurs réponses:", 
                                        options,
                                        default=current_answers,
                                        key=current_answer_key)
                
                st.session_state.ecn_answers[current_question_global]['selected'] = selected
            
            # ✅ Navigation entre questions - VERSION STABLE
            # ✅ Navigation entre questions - VERSION GRILLE COMPACTE
            st.markdown("---")
            nav_col1, nav_col3 = st.columns([1, 1])

            # ⬅️ Question précédente
            with nav_col1:
                if current_question_global > 0:
                    if st.button("⬅️ Précédente", use_container_width=True, key=f"prev_btn_{current_question_global}"):
                        st.session_state.ecn_current_question -= 1
                        new_section = st.session_state.ecn_current_question // 30
                        if new_section != current_section:
                            st.session_state.ecn_current_section = new_section
                        st.rerun()

            # ➡️ Question suivante ou Terminer
            with nav_col3:
                if current_question_global < len(session['questions']) - 1:
                    if st.button("Suivante ➡️", use_container_width=True, key=f"next_btn_{current_question_global}"):
                        st.session_state.ecn_current_question += 1
                        new_section = st.session_state.ecn_current_question // 30
                        if new_section != current_section:
                            st.session_state.ecn_current_section = new_section
                        st.rerun()
                else:
                    if st.button("✅ Terminer", type="primary", use_container_width=True, key="finish_btn"):
                        st.session_state.ecn_simulation_finished = True
                        st.session_state.ecn_end_time = time.time()
                        time_taken = st.session_state.ecn_end_time - st.session_state.ecn_start_time
                        results = simulator.calculate_ecn_score(st.session_state.ecn_answers, session['questions'])
                        st.session_state.ecn_results = {
                            'session': session,
                            'results': results,
                            'time_taken': time_taken,
                            'user_answers': st.session_state.ecn_answers
                        }
                        st.rerun()
            # 🟢 BARRE DE PROGRESSION PAR SECTION
            st.markdown("---")
            st.markdown("### 📂 Progression par section")

            section_titles = [
                "Médecine Interne",
                "Urgences",
                "Diagnostic & Thérapeutique",
                "Situations Complexes"
            ]

            section_cols = st.columns(4)
            questions_per_section = 30

            for i, col in enumerate(section_cols):
                with col:
                    start = i * questions_per_section
                    end = min(start + questions_per_section, len(st.session_state.ecn_answers))
                    answered = sum(1 for ans in st.session_state.ecn_answers[start:end] if ans.get('selected'))
                    progress = answered / (end - start) if end - start > 0 else 0

                    # Couleur selon progression
                    if progress == 1:
                        color = "#198754"  # vert complet
                    elif progress > 0:
                        color = "#ffc107"  # jaune partiel
                    else:
                        color = "#6c757d"  # gris vide

                    progress_pct = int(progress * 100)
                    section_label = f"Section {i+1} ({progress_pct}%)"

                    if st.button(section_label, key=f"section_progress_{i}", use_container_width=True):
                        st.session_state.ecn_current_section = i
                        st.session_state.ecn_current_question = start
                        st.rerun()

                    st.markdown(
                        f"<style>div[data-testid='stButton'][key='section_progress_{i}'] button{{background-color:{color};color:white;border-radius:8px;font-weight:bold;}}</style>",
                        unsafe_allow_html=True
                    )


            # 🧭 NAVIGATION RAPIDE PAR GRILLE
            st.markdown("---")
            st.markdown("### 🧭 Navigation rapide")

            total_questions = len(session['questions'])
            cols_per_row = 10  # 10 boutons par ligne
            rows = (total_questions // cols_per_row) + (1 if total_questions % cols_per_row != 0 else 0)

            for row in range(rows):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    q_index = row * cols_per_row + col_idx
                    if q_index >= total_questions:
                        break

                    # Statut visuel : déjà répondu / actuelle / vide
                    answer_data = st.session_state.ecn_answers[q_index]
                    if answer_data.get('selected'):
                        style = "background-color:#198754;color:white;"  # vert = répondu
                    elif q_index == current_question_global:
                        style = "background-color:#0d6efd;color:white;"  # bleu = actuelle
                    else:
                        style = "background-color:#f8f9fa;color:black;"  # neutre

                    with col:
                        if st.button(f"{q_index+1}", key=f"nav_q_{q_index}", use_container_width=True):
                            st.session_state.ecn_current_question = q_index
                            st.session_state.ecn_current_section = q_index // 30
                            st.rerun()
                        st.markdown(
                            f"<style>div[data-testid='stButton'][key='nav_q_{q_index}'] button{{{style}border-radius:6px;font-weight:bold;}}</style>",
                            unsafe_allow_html=True
                        )


            
        # Bouton d'abandon
            if st.button("⏹️ Abandonner", type="secondary", use_container_width=True, key="abandon_btn"):
                st.session_state.ecn_simulation_active = False
                st.info("Simulation abandonnée")
                st.rerun()
        
        # AFFICHAGE DES RÉSULTATS
        elif st.session_state.get('ecn_simulation_finished') and st.session_state.get('ecn_results'):
            results_data = st.session_state.ecn_results
            session = results_data['session']
            results = results_data['results']
            time_taken = results_data['time_taken']
            
            st.markdown("## 📊 Résultats de la Simulation ECN")
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎯 Score final", f"{results['percentage']:.1f}%")
            with col2:
                st.metric("📈 Note", results['grade'])
            with col3:
                status_color = "🟢" if results['passed'] else "🔴"
                st.metric("✅ Statut", f"{status_color} {'Réussi' if results['passed'] else 'Échec'}")
            with col4:
                st.metric("⏱️ Temps", f"{int(time_taken//60)}min {int(time_taken%60)}s")
            
            # Sauvegarde des résultats
            if st.button("💾 Sauvegarder les résultats", key="save_results_btn"):
                if db.save_ecn_simulation(st.session_state.username, results_data):
                    st.success("✅ Résultats sauvegardés!")
                    
                    # Vérification des badges
                    new_badges = badge_mgr.check_ecn_badges(st.session_state.username, results_data)
                    if new_badges:
                        st.balloons()
                        st.success("🎖️ Nouveaux badges débloqués!")
                        for badge in new_badges:
                            st.markdown(f'<span class="badge badge-gold">{badge}</span>', unsafe_allow_html=True)
                else:
                    st.error("❌ Erreur lors de la sauvegarde")
            
            # Boutons d'action
            col_new, col_details, col_home = st.columns(3)
            with col_new:
                if st.button("🔄 Nouvelle simulation", use_container_width=True, key="new_sim_btn"):
                    # Réinitialiser seulement les variables ECN
                    for key in [k for k in st.session_state.keys() if k.startswith('ecn_')]:
                        del st.session_state[key]
                    st.rerun()
            
            with col_details:
                if st.button("📊 Détail des réponses", use_container_width=True, key="details_btn"):
                    st.session_state.show_ecn_details = True
                    st.rerun()
            
            with col_home:
                if st.button("🏠 Accueil", use_container_width=True, key="home_btn"):
                    for key in [k for k in st.session_state.keys() if k.startswith('ecn_')]:
                        del st.session_state[key]
                    st.rerun()
            
            # Boutons d'action
            col_new, col_details, col_home = st.columns(3)
            with col_new:
                if st.button("🔄 Nouvelle simulation", use_container_width=True, key="new_sim_btn"):
                    # Réinitialiser seulement les variables ECN
                    for key in [k for k in st.session_state.keys() if k.startswith('ecn_')]:
                        del st.session_state[key]
                    st.rerun()
            
            with col_details:
                if st.button("📊 Détail des réponses", use_container_width=True, key="details_btn"):
                    st.session_state.show_ecn_details = True
                    st.rerun()
            
            with col_home:
                if st.button("🏠 Accueil", use_container_width=True, key="home_btn"):
                    for key in [k for k in st.session_state.keys() if k.startswith('ecn_')]:
                        del st.session_state[key]
                    st.rerun()
    
    # GESTION DES AUTRES ONGLETS
    with tab2:
        st.markdown("### 📈 Mes Statistiques ECN")
        stats = db.get_user_ecn_stats(st.session_state.username)
        
        if stats and stats.get('total_simulations', 0) > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Simulations", stats['total_simulations'])
            with col2:
                st.metric("Score moyen", f"{stats.get('average_score', 0):.1f}%")
            with col3:
                st.metric("Meilleur score", f"{stats.get('best_score', 0):.1f}%")
            with col4:
                success_rate = (stats.get('passed_count', 0) / stats['total_simulations'] * 100) if stats['total_simulations'] > 0 else 0
                st.metric("Taux réussite", f"{success_rate:.1f}%")
        else:
            st.info("Aucune simulation ECN complétée")
    
    with tab3:
        st.markdown("### 🏅 Classement ECN")
        leaderboard = db.get_ecn_leaderboard(limit=10)
        
        if leaderboard:
            for i, student in enumerate(leaderboard):
                cols = st.columns([1, 3, 2, 2])
                with cols[0]:
                    if i == 0: st.markdown("🥇")
                    elif i == 1: st.markdown("🥈") 
                    elif i == 2: st.markdown("🥉")
                    else: st.markdown(f"**#{i+1}**")
                with cols[1]:
                    st.write(student['username'])
                with cols[2]:
                    st.write(f"**{student['best_score']:.1f}%**")
                with cols[3]:
                    st.write(f"{student['simulations_count']} simus")
        else:
            st.info("Aucun classement disponible")
    
    with tab4:
        st.markdown("### ℹ️ Guide des Simulations ECN")
        st.markdown("""
        **Déroulement:**
        - 4 sections de 30 questions
        - Navigation libre entre les questions
        - Timer de 60 minutes
        - Score avec pénalités pour mauvaises réponses
        
        **Conseils:**
        - Gérez votre temps (30s/question)
        - Passez les questions difficiles
        - Revenez à la fin si possible
        """)
# Footer
st.markdown("---")
st.markdown(
    "**ECN Prep** - Plateforme de préparation aux ECN pour les étudiants en santé, entièrement gratuite | "
    "Développé par Limack0 © 2025, Tous droits réservés. mbeogo@gmail.com"
)