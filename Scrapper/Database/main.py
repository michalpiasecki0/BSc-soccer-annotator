import sqlite3


def main():
    conn = sqlite3.connect('annotations.db')
    c = conn.cursor()
    c.execute('DROP TABLE annotations')

    c.execute("""
            CREATE TABLE annotations (
            x_cor REAL NOT NULL,
            y_cor REAL NOT NULL,
            time_start REAL NOT NULL,
            time_finish REAL,
            match TEXT ,
            match_date TEXT,
            annotator_name TEXT,
            action_type TEXT NOT NULL,
            description TEXT
            
            )   
            """)

if __name__ == "__main__":
    main()