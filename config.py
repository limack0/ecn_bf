import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Configuration SQLite — remplace la configuration PostgreSQL"""
    db_path: str = os.getenv("SQLITE_DB_PATH", "database.db")


@dataclass
class AppConfig:
    specialties: List[str] = None
    competition_time: int = 600  # 10 minutes en secondes
    max_questions: int = 50

    def __post_init__(self):
        if self.specialties is None:
            self.specialties = [
                "cardiologie", "pneumologie", "neurologie",
                "gastroenterologie", "rhumatologie", "nephrologie",
                "endocrinologie", "hematologie", "infectiologie"
            ]


@dataclass
class ECNConfig:
    simulation_duration: int = 3600  # 60 minutes
    questions_per_session: int = 120
    specialties_distribution: Dict[str, int] = None
    break_duration: int = 600  # 10 minutes
    passing_score: int = 70  # pourcentage de réussite

    def __post_init__(self):
        if self.specialties_distribution is None:
            self.specialties_distribution = {
                "cardiologie": 15,
                "pneumologie": 12,
                "neurologie": 10,
                "gastroenterologie": 10,
                "rhumatologie": 8,
                "nephrologie": 8,
                "endocrinologie": 8,
                "hematologie": 8,
                "infectiologie": 10,
                "urgences": 11
            }


class BadgeSystem:
    BADGES = {
        "debutant": {"name": "Débutant", "threshold": 10, "color": "badge-secondary"},
        "intermediaire": {"name": "Intermédiaire", "threshold": 50, "color": "badge-primary"},
        "expert": {"name": "Expert", "threshold": 100, "color": "badge-info"},
        "champion": {"name": "Champion", "threshold": 200, "color": "badge-warning"},
        "maitre": {"name": "Maître", "threshold": 500, "color": "badge-gold"},
        "clinician": {"name": "Excellent Clinicien", "threshold": 300, "color": "badge-success"},
        "rapide": {"name": "Rapide", "threshold": 150, "color": "badge-danger"},
        "simulateur": {"name": "Simulateur ECN", "threshold": 1, "color": "badge-info"},
        "excellent": {"name": "Excellent", "threshold": 85, "color": "badge-success"},
        "marathonien": {"name": "Marathonien", "threshold": 5, "color": "badge-warning"},
        "podium": {"name": "Sur le Podium", "threshold": 3, "color": "badge-gold"},
    }
