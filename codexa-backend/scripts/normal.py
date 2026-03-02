#!/usr/bin/env python3
"""Seed the database with sample data"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, SessionLocal
from app.models import Base, LearningPath, Topic, Challenge
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_learning_paths():
    """Create sample learning paths"""
    db = SessionLocal()
    
    try:
        # Python Basics Path
        python_basics = LearningPath(
            title="Python Fundamentals",
            description="Learn Python programming from scratch",
            difficulty="beginner",
            estimated_hours=20,
            is_published=True
        )
        db.add(python_basics)
        db.commit()
        db.refresh(python_basics)
        
        # Add topics
        topics_data = [
            {
                "title": "Variables and Data Types",
                "description": "Learn about variables, strings, numbers, and booleans",
                "order_index": 1,
                "content": "# Variables in Python\n\nVariables store data...",
            },
            {
                "title": "Control Flow",
                "description": "If statements, loops, and logic",
                "order_index": 2,
                "content": "# Control Flow\n\nControl flow determines...",
            },
            {
                "title": "Functions",
                "description": "Define and use functions",
                "order_index": 3,
                "content": "# Functions\n\nFunctions are reusable...",
            },
        ]
        
        for topic_data in topics_data:
            topic = Topic(
                learning_path_id=python_basics.id,
                **topic_data
            )
            db.add(topic)
        
        db.commit()
        logger.info("✅ Learning paths seeded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🌱 Seeding database...")
    seed_learning_paths()
    logger.info("✅ Seeding complete!")