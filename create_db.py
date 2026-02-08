import sqlite3

def create_database():
    db_name = "chatbot_feedback.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test (
        id INTEGER PRIMARY KEY,         
        agent_id INTEGER NOT NULL,      
        timestamp INTEGER,          
        prompt TEXT NOT NULL,
        response TEXT NOT NULL,
        response_feedback TEXT NOT NULL,  
        comment TEXT     
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY, 
        test_id INTEGER NOT NULL,
        citation_index INTEGER NOT NULL,                  
        content TEXT NOT NULL,
        chunk_feedback TEXT NOT NULL,                       
        FOREIGN KEY (test_id) REFERENCES test(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' and tables created successfully.")

if __name__ == "__main__":
    create_database()