import json
import os
import random
from typing import Dict, List, Optional, Tuple
import streamlit as st
from typing import List, Dict

class QuizManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.quizzes = {}
        self.clinical_cases = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Charge tous les fichiers JSON disponibles"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            st.warning(f"Le dossier {self.data_dir} a été créé. Veuillez y ajouter vos fichiers JSON.")
            return
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.json'):
                specialty = file.replace('.json', '')
                try:
                    with open(os.path.join(self.data_dir, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.quizzes[specialty] = data.get('quizzes', [])
                        self.clinical_cases[specialty] = data.get('clinical_cases', [])
                except Exception as e:
                    st.error(f"Erreur lors du chargement de {file}: {e}")
    
    def get_specialties(self) -> List[str]:
        return list(self.quizzes.keys())
    
    def get_quiz_questions(self, specialty: str, num_questions: int = 5) -> List[Dict]:
        """Récupère des questions aléatoires pour un quiz"""
        if specialty not in self.quizzes:
            return []
        
        questions = self.quizzes[specialty].copy()
        random.shuffle(questions)
        return questions[:num_questions]
    
    def get_progressive_clinical_case(self, specialty: str, case_id: Optional[int] = None) -> Dict:
        """Récupère un dossier clinique progressif"""
        if specialty not in self.clinical_cases:
            return {}
        
        cases = self.clinical_cases[specialty]
        if not cases:
            return {}
        
        if case_id is None:
            return random.choice(cases)
        else:
            return cases[case_id % len(cases)]

    def calculate_score(self, user_answers: List[Dict], questions: List[Dict]) -> int:
        """Calcule le score basé sur les réponses utilisateur."""
        score = 0

        for i, question in enumerate(questions):
            if i >= len(user_answers):
                continue  # sécurité : trop peu de réponses

            user_answer = user_answers[i]
            selected = user_answer.get("selected", [])
            if isinstance(selected, str):
                selected = [selected]  # uniformiser le format

            correct_answers = [opt["text"] for opt in question["options"] if opt.get("correct", False)]

            # ---- Type "single" ----
            if question["type"] == "single":
                if selected and selected[0] in correct_answers:
                    score += 1

            # ---- Type "multiple" ----
            elif question["type"] == "multiple":
                selected_correct = sum(1 for ans in selected if ans in correct_answers)
                selected_incorrect = sum(1 for ans in selected if ans not in correct_answers)

                if selected_correct == len(correct_answers) and selected_incorrect == 0:
                    score += 2  # toutes correctes
                elif selected_correct > 0:
                    score += 1  # partiellement correct

        return score

    
    def validate_clinical_case_step(self, case: Dict, step_index: int, user_answer: str) -> Tuple[bool, str, str]:
        """Valide la réponse à une étape du dossier clinique"""
        if step_index >= len(case['steps']):
            return False, "", "Étape invalide"
        
        step = case['steps'][step_index]
        
        if 'correct_answer' in step:
            # Validation simple avec réponse correcte prédéfinie
            correct_answer = step['correct_answer']
            if isinstance(user_answer, list):
                user_answer = user_answer[0] if user_answer else ""
            is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
            explanation = step.get('explanation', '')
            return is_correct, correct_answer, explanation
        
        elif 'correct_options' in step:
            # Validation pour les questions à choix multiples
            correct_options = step['correct_options']
            user_selection = user_answer if isinstance(user_answer, list) else [user_answer]
            is_correct = set(user_selection) == set(correct_options)
            explanation = step.get('explanation', '')
            return is_correct, ", ".join(correct_options), explanation
        
        else:
            # Pas de validation automatique pour les questions ouvertes
            return True, "Réponse libre", step.get('explanation', '')
    
    def calculate_clinical_case_score(self, case: Dict, user_answers: List[Dict]) -> Dict:
        """Calcule le score pour un dossier clinique complet"""
        total_steps = len([step for step in case['steps'] if 'question' in step])
        correct_steps = 0
        detailed_feedback = []
        
        for user_answer_data in user_answers:
            step_index = user_answer_data['step']
            if step_index < len(case['steps']):
                step = case['steps'][step_index]
                if 'question' in step:
                    is_correct, correct_answer, explanation = self.validate_clinical_case_step(
                        case, step_index, user_answer_data['answer']
                    )
                    if is_correct:
                        correct_steps += 1
                    
                    detailed_feedback.append({
                        'step': step_index,
                        'user_answer': user_answer_data['answer'],
                        'correct_answer': correct_answer,
                        'is_correct': is_correct,
                        'explanation': explanation,
                        'question': step['question'],
                        'title': step['title']
                    })
        
        score_percentage = (correct_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            'total_steps': total_steps,
            'correct_steps': correct_steps,
            'score_percentage': score_percentage,
            'detailed_feedback': detailed_feedback
        }