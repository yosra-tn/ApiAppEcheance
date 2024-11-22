from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_Url = "postgresql://postgres:wtmy%40456@localhost/BDAppEcheance"
engine = create_engine(DB_Url)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()
def init_db():
    print("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")
