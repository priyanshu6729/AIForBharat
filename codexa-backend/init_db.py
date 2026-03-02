"""Initialize database tables - ONLY for the frontend app models."""
from app.db import Base, engine

# Import ONLY the frontend app models (not libs.common)
from app.models.models import (
    User, Session, CodeSnapshot, GuidanceLog, 
    LearningPath, Lesson, Progress, Achievement
)

def init_db():
    """Create all database tables."""
    print("🔄 Creating database tables for FRONTEND app...")
    try:
        # Clear any previously registered tables
        Base.metadata.clear()
        
        # Explicitly register only our models
        tables_to_create = [
            User.__table__,
            Session.__table__,
            CodeSnapshot.__table__,
            GuidanceLog.__table__,
            LearningPath.__table__,
            Lesson.__table__,
            Progress.__table__,
            Achievement.__table__,
        ]
        
        # Create only these tables
        for table in tables_to_create:
            table.create(bind=engine, checkfirst=True)
        
        print("✅ Database tables created successfully!")
        
        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n📊 Found {len(tables)} tables in database:")
        
        for table_name in ["users", "sessions", "code_snapshots", "guidance_logs", 
                          "learning_paths", "lessons", "progress", "achievements"]:
            if table_name in tables:
                print(f"  ✓ {table_name}")
                columns = inspector.get_columns(table_name)
                for col in columns:
                    print(f"    • {col['name']}: {col['type']}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    init_db()