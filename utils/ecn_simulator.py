import random
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import streamlit as st
from config import ECNConfig

class ECNSimulator:
    def __init__(self, quiz_manager):
        self.config = ECNConfig()
        self.quiz_manager = quiz_manager
        self.current_simulation = None
    
    def generate_simulation_session(self) -> Dict:
        """Génère une session de simulation ECN complète"""
        all_questions = []
        
        # Collecter les questions selon la distribution par spécialité
        for specialty, count in self.config.specialties_distribution.items():
            specialty_questions = self.quiz_manager.get_quiz_questions(specialty, count)
            all_questions.extend(specialty_questions)
        
        # Mélanger les questions
        random.shuffle(all_questions)
        
        # Structurer la session
        session = {
            'id': f"ecn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'title': "Simulation ECN Complète",
            'duration': self.config.simulation_duration,
            'total_questions': len(all_questions),
            'questions': all_questions,
            'created_at': datetime.now(),
            'sections': self._create_sections(all_questions),
            'breaks': [1200, 2400]  # Pauses après 20 et 40 minutes
        }
        
        return session
    
    def _create_sections(self, questions: List[Dict]) -> List[Dict]:
        """Crée des sections thématiques pour la simulation"""
        sections = []
        questions_per_section = 30
        section_titles = [
            "Section 1 : Médecine Interne et Spécialités",
            "Section 2 : Pathologies Aiguës et Urgences", 
            "Section 3 : Diagnostic et Thérapeutique",
            "Section 4 : Situations Complexes"
        ]
        
        for i, title in enumerate(section_titles):
            start_idx = i * questions_per_section
            end_idx = start_idx + questions_per_section
            section_questions = questions[start_idx:end_idx]
            
            sections.append({
                'title': title,
                'questions': section_questions,
                'duration': self.config.simulation_duration // 4,
                'order': i + 1
            })
        
        return sections
    
    def calculate_ecn_score(self, user_answers: List[Dict], questions: List[Dict]) -> Dict:
        """Calcule le score selon le barème ECN"""
        total_score = 0
        max_score = len(questions) * 2  # 2 points par question parfaite
        detailed_results = []
        
        for i, question in enumerate(questions):
            user_answer = user_answers[i] if i < len(user_answers) else {}
            correct_answers = [opt for opt in question['options'] if opt.get('correct', False)]
            
            question_score = 0
            feedback = ""
            
            if question['type'] == 'single':
                selected = user_answer.get('selected', '')
                if selected == correct_answers[0]['text']:
                    question_score = 2
                    feedback = "Bonne réponse"
                elif selected:
                    question_score = -0.5  # Pénalité pour mauvaise réponse
                    feedback = "Mauvaise réponse (-0.5 point)"
                else:
                    feedback = "Non répondu (0 point)"
            
            elif question['type'] == 'multiple':
                selected = user_answer.get('selected', [])
                correct_texts = [opt['text'] for opt in correct_answers]
                
                correct_count = sum(1 for ans in selected if ans in correct_texts)
                incorrect_count = sum(1 for ans in selected if ans not in correct_texts)
                
                if correct_count == len(correct_texts) and incorrect_count == 0:
                    question_score = 2
                    feedback = "Réponse parfaite"
                elif correct_count > 0:
                    # Score proportionnel aux bonnes réponses moins les mauvaises
                    question_score = max(0, (correct_count * 0.5) - (incorrect_count * 0.5))
                    feedback = f"{correct_count} bonne(s) réponse(s), {incorrect_count} mauvaise(s)"
                else:
                    question_score = 0
                    feedback = "Aucune bonne réponse"
            
            total_score += question_score
            
            detailed_results.append({
                'question_number': i + 1,
                'question_text': question['question'][:100] + "...",
                'user_answer': user_answer.get('selected', 'Non répondu'),
                'correct_answer': [opt['text'] for opt in correct_answers],
                'score': question_score,
                'feedback': feedback,
                'explanation': question.get('explanation', '')
            })
        
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        return {
            'raw_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'passed': percentage >= self.config.passing_score,
            'detailed_results': detailed_results,
            'grade': self._calculate_grade(percentage)
        }
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calcule la mention selon le score"""
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Très Bien"
        elif percentage >= 70:
            return "Bien"
        elif percentage >= 60:
            return "Assez Bien"
        else:
            return "Insuffisant"
    
    def get_simulation_statistics(self, username: str) -> Dict:
        """Récupère les statistiques de simulation d'un utilisateur"""
        # Cette méthode sera implémentée dans database.py
        return {
            'simulations_completed': 0,
            'average_score': 0,
            'best_score': 0,
            'time_spent': 0
        }