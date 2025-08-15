# create_tables.py
"""
Creates database `attendance_db` and tables:
- admin
- teachers
- classes
- students
- attendance

Also inserts:
- default admin (username: admin, password: admin123)
- 5 teachers (teacher1..teacher5 with password teach123)
- 8 classes (Class 1 .. Class 8)
- 50 students per class (total 400 sample students)

Run:
    python create_tables.py
"""

import mysql.connector
from mysql.connector import errorcode
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from werkzeug.security import generate_password_hash
import sys

def create_database(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET 'utf8mb4'")
    cursor.execute(f"USE `{DB_NAME}`")

def create_tables(cursor):
    # admin table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)

    # teachers table (class_assigned as comma-separated values for simplicity)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        class_assigned VARCHAR(100), -- e.g. '1,2'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)

    # classes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        class_name VARCHAR(50) NOT NULL UNIQUE
    ) ENGINE=InnoDB;
    """)

    # students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        roll_no VARCHAR(50),
        class_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    # attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        date DATE NOT NULL,
        status ENUM('Present','Absent') NOT NULL,
        marked_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE KEY uniq_student_date (student_id, date)
    ) ENGINE=InnoDB;
    """)

def insert_default_admin(cursor, conn):
    default_admin = "admin"
    default_pass = "admin123"
    cursor.execute("SELECT id FROM admin WHERE username=%s", (default_admin,))
    if cursor.fetchone() is None:
        hashed = generate_password_hash(default_pass)
        cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (default_admin, hashed))
        conn.commit()
        print(f"Default admin created -> username: {default_admin}, password: {default_pass}")
    else:
        print("Default admin already exists.")

def insert_classes(cursor, conn):
    cursor.execute("SELECT COUNT(*) FROM classes")
    if cursor.fetchone()[0] == 0:
        classes = [(f"Class {i}",) for i in range(1,9)]  # Class 1..Class 8
        cursor.executemany("INSERT INTO classes (class_name) VALUES (%s)", classes)
        conn.commit()
        print("Inserted classes 1..8")
    else:
        print("Classes already inserted.")

def insert_teachers(cursor, conn):
    # Define teachers and their assigned classes (comma-separated)
    teacher_defs = [
    ("Rajesh Kumar", "teacher1", "1,2"),
    ("Sneha Gupta", "teacher2", "3,4"),
    ("Vikram Singh", "teacher3", "5"),
    ("Pooja Sharma", "teacher4", "6,7"),
    ("Amit Verma", "teacher5", "8"),
  ]
    default_pass = "teach123"
    cursor.execute("SELECT COUNT(*) FROM teachers")
    if cursor.fetchone()[0] == 0:
        to_insert = []
        for name, username, class_assigned in teacher_defs:
            hashed = generate_password_hash(default_pass)
            to_insert.append((name, username, hashed, class_assigned))
        cursor.executemany("INSERT INTO teachers (name, username, password, class_assigned) VALUES (%s,%s,%s,%s)", to_insert)
        conn.commit()
        print("Inserted 5 teachers with default password 'teach123'")
        print("Teachers usernames: teacher1 .. teacher5")
    else:
        print("Teachers already exist.")

def insert_students(cursor, conn):
    # For each class (1..8) insert 50 students
    cursor.execute("SELECT id FROM classes ORDER BY id")
    class_rows = cursor.fetchall()
    if not class_rows:
        print("No classes found — cannot insert students.")
        return

    # check existing student count
    cursor.execute("SELECT COUNT(*) FROM students")
    existing = cursor.fetchone()[0]
    if existing >= 1:
        print(f"{existing} students already exist — skipping student insertion.")
        return

    to_insert = []
    for class_row in class_rows:
        class_id = class_row[0]
        # generate 50 students
        for i in range(1, 51):
            roll = f"C{class_id:02d}-{i:03d}"   # e.g. C01-001
            name = f"Student_C{class_id}_{i}"
            to_insert.append((name, roll, class_id))

    # Insert in batches
    batch_size = 200
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i:i+batch_size]
        cursor.executemany("INSERT INTO students (name, roll_no, class_id) VALUES (%s, %s, %s)", batch)
        conn.commit()

    print(f"Inserted {len(to_insert)} students (50 per class for 8 classes).")

def main():
    try:
        # connect without DB to create DB if not exists
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        conn.autocommit = True
        cursor = conn.cursor()
        create_database(cursor)
        cursor.close()
        conn.close()

        # connect to the created DB
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()

        create_tables(cursor)
        insert_default_admin(cursor, conn)
        insert_classes(cursor, conn)
        insert_teachers(cursor, conn)
        insert_students(cursor, conn)

        cursor.close()
        conn.close()
        print("Database setup completed successfully.")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("ERROR: Invalid MySQL credentials. Check DB_USER & DB_PASSWORD in config.py")
        else:
            print("MySQL Error:", err)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
