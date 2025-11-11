import json
import os

def create_data_directory():
    """Crée le répertoire data s'il n'existe pas"""
    if not os.path.exists('data'):
        os.makedirs('data')
        print("✅ Répertoire 'data' créé")

def generate_specialty_files():
    """Génère tous les fichiers de spécialités"""
    specialties_data = {
        'cardiologie': {
            'quizzes': [
                {
                    'question': 'Quelle est la première intention thérapeutique dans l\'infarctus du myocarde avec sus-décalage du segment ST?',
                    'type': 'single',
                    'options': [
                        {'text': 'Aspirine + Clopidogrel', 'correct': False},
                        {'text': 'Angioplastie primaire', 'correct': True},
                        {'text': 'Thrombolyse', 'correct': False},
                        {'text': 'Traitement médical seul', 'correct': False}
                    ],
                    'explanation': 'L\'angioplastie primaire est le traitement de première intention lorsqu\'elle est disponible dans les délais (<90 minutes).'
                }
            ],
            'clinical_cases': [
                {
                    'title': 'Douleur thoracique chez un homme de 55 ans',
                    'difficulty': 'Intermédiaire',
                    'steps': [
                        {
                            'title': 'Présentation initiale',
                            'content': 'Monsieur D., 55 ans, se présente aux urgences pour une douleur thoracique rétro-sternale constrictive survenue au repos, irradiant dans le bras gauche, évoluant depuis 45 minutes. Antécédents : HTA, tabagisme actif (20 PA), dyslipidémie.',
                            'type': 'multiple_choice',
                            'question': 'Quels examens demandez-vous en priorité?',
                            'options': ['ECG', 'Biologie cardiaque', 'Radiographie thoracique', 'Échocardiographie'],
                            'correct_answer': 'ECG',
                            'explanation': 'L\'ECG est l\'examen de première intention devant toute douleur thoracique évocatrice de syndrome coronarien aigu.'
                        }
                    ],
                    'solution': '**Diagnostic final:** Syndrome coronarien aigu avec sus-décalage du segment ST (STEMI) antérieur.'
                }
            ]
        }
    }
    
    # Générer tous les fichiers
    for specialty, data in specialties_data.items():
        filename = f"data/{specialty}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Fichier {filename} généré")
    
    print("🎉 Tous les fichiers de données ont été générés avec succès!")

if __name__ == "__main__":
    create_data_directory()
    generate_specialty_files()