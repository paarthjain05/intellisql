import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_college_database():
    """
    Create a college database with 5 related tables:
    1. STUDENTS - Student information
    2. COURSES - Course catalog
    3. PROFESSORS - Faculty information
    4. ENROLLMENTS - Student-Course relationships
    5. DEPARTMENTS - Academic departments
    """
    
    if os.path.exists("college.db"):
        os.remove("college.db")
        print("Removed existing database")
    
    connection = sqlite3.connect("college.db")
    cursor = connection.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("Creating college database with 5 related tables...\n")
    
    departments_table = '''
    CREATE TABLE DEPARTMENTS (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name VARCHAR(50) NOT NULL UNIQUE,
        dept_head VARCHAR(50),
        building VARCHAR(50),
        budget DECIMAL(12,2),
        established_year INTEGER,
        phone VARCHAR(15),
        email VARCHAR(100)
    )
    '''
    cursor.execute(departments_table)
    print("✓ Created DEPARTMENTS table")
    
    professors_table = '''
    CREATE TABLE PROFESSORS (
        prof_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        dept_id INTEGER NOT NULL,
        designation VARCHAR(50),
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(15),
        office_room VARCHAR(20),
        hire_date DATE,
        salary DECIMAL(10,2),
        research_area VARCHAR(200),
        FOREIGN KEY (dept_id) REFERENCES DEPARTMENTS(dept_id) ON DELETE CASCADE
    )
    '''
    cursor.execute(professors_table)
    print("✓ Created PROFESSORS table")
    
    courses_table = '''
    CREATE TABLE COURSES (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code VARCHAR(15) UNIQUE NOT NULL,
        course_name VARCHAR(100) NOT NULL,
        dept_id INTEGER NOT NULL,
        prof_id INTEGER,
        credits INTEGER CHECK(credits > 0),
        semester VARCHAR(20),
        year INTEGER,
        max_students INTEGER DEFAULT 50,
        room VARCHAR(20),
        schedule VARCHAR(50),
        FOREIGN KEY (dept_id) REFERENCES DEPARTMENTS(dept_id) ON DELETE CASCADE,
        FOREIGN KEY (prof_id) REFERENCES PROFESSORS(prof_id) ON DELETE SET NULL
    )
    '''
    cursor.execute(courses_table)
    print("✓ Created COURSES table")
    
    students_table = '''
    CREATE TABLE STUDENTS (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        student_number VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(15),
        major_dept_id INTEGER,
        year_level INTEGER CHECK(year_level >= 1 AND year_level <= 4),
        gpa DECIMAL(3,2) CHECK(gpa >= 0.0 AND gpa <= 4.0),
        enrollment_date DATE,
        graduation_date DATE,
        address TEXT,
        date_of_birth DATE,
        FOREIGN KEY (major_dept_id) REFERENCES DEPARTMENTS(dept_id) ON DELETE SET NULL
    )
    '''
    cursor.execute(students_table)
    print("✓ Created STUDENTS table")
    
    enrollments_table = '''
    CREATE TABLE ENROLLMENTS (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        semester VARCHAR(20) NOT NULL,
        year INTEGER NOT NULL,
        grade VARCHAR(5),
        enrollment_date DATE DEFAULT CURRENT_DATE,
        final_score DECIMAL(5,2),
        attendance_percentage DECIMAL(5,2) DEFAULT 100.0,
        status VARCHAR(20) DEFAULT 'Active',
        FOREIGN KEY (student_id) REFERENCES STUDENTS(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES COURSES(course_id) ON DELETE CASCADE,
        UNIQUE(student_id, course_id, semester, year)
    )
    '''
    cursor.execute(enrollments_table)
    print("✓ Created ENROLLMENTS table")
    
    print("\n" + "="*50)
    print("POPULATING TABLES WITH SAMPLE DATA")
    print("="*50)
    
    departments_data = [
        ('Computer Science', 'Dr. Sarah Johnson', 'Tech Building A', 750000.00, 1985, '555-0101', 'cs@college.edu'),
        ('Mathematics', 'Dr. Michael Brown', 'Science Building', 450000.00, 1970, '555-0102', 'math@college.edu'),
        ('Business Administration', 'Prof. Emily Davis', 'Business Center', 600000.00, 1978, '555-0103', 'business@college.edu'),
        ('Engineering', 'Dr. David Kumar', 'Engineering Complex', 900000.00, 1980, '555-0104', 'engineering@college.edu'),
        ('Psychology', 'Dr. Lisa Anderson', 'Social Sciences Hall', 350000.00, 1975, '555-0105', 'psych@college.edu')
    ]
    cursor.executemany('''INSERT INTO DEPARTMENTS 
                         (dept_name, dept_head, building, budget, established_year, phone, email) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', departments_data)
    print("✓ Inserted 5 departments")
    
    professors_data = [
        ('Dr. John Smith', 1, 'Professor', 'john.smith@college.edu', '555-1001', 'TA-201', '2015-08-15', 85000.00, 'Machine Learning, AI'),
        ('Dr. Maria Garcia', 1, 'Associate Professor', 'maria.garcia@college.edu', '555-1002', 'TA-203', '2018-01-10', 75000.00, 'Database Systems'),
        ('Dr. Robert Wilson', 2, 'Professor', 'robert.wilson@college.edu', '555-1003', 'SB-101', '2012-09-01', 80000.00, 'Applied Mathematics'),
        ('Prof. Jennifer Lee', 3, 'Assistant Professor', 'jennifer.lee@college.edu', '555-1004', 'BC-305', '2020-08-20', 70000.00, 'Marketing Strategy'),
        ('Dr. Ahmed Hassan', 4, 'Professor', 'ahmed.hassan@college.edu', '555-1005', 'EC-401', '2010-07-15', 90000.00, 'Structural Engineering'),
        ('Dr. Rachel Green', 5, 'Associate Professor', 'rachel.green@college.edu', '555-1006', 'SSH-201', '2017-01-15', 72000.00, 'Cognitive Psychology'),
        ('Dr. Kevin Chen', 1, 'Assistant Professor', 'kevin.chen@college.edu', '555-1007', 'TA-205', '2021-08-01', 68000.00, 'Cybersecurity'),
        ('Prof. Linda Taylor', 2, 'Associate Professor', 'linda.taylor@college.edu', '555-1008', 'SB-103', '2016-09-10', 74000.00, 'Statistics')
    ]
    cursor.executemany('''INSERT INTO PROFESSORS 
                         (name, dept_id, designation, email, phone, office_room, hire_date, salary, research_area) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', professors_data)
    print("✓ Inserted 8 professors")
    
    courses_data = [
        ('CS101', 'Introduction to Programming', 1, 1, 4, 'Fall', 2024, 60, 'TA-Lab1', 'MWF 9:00-10:00'),
        ('CS201', 'Data Structures', 1, 1, 4, 'Spring', 2024, 45, 'TA-Lab2', 'TTh 10:30-12:00'),
        ('CS301', 'Database Systems', 1, 2, 3, 'Fall', 2024, 40, 'TA-Lab3', 'MWF 2:00-3:00'),
        ('CS401', 'Machine Learning', 1, 1, 4, 'Spring', 2024, 30, 'TA-Lab4', 'TTh 1:00-2:30'),
        ('MATH101', 'Calculus I', 2, 3, 4, 'Fall', 2024, 80, 'SB-201', 'MWF 8:00-9:00'),
        ('MATH201', 'Statistics', 2, 8, 3, 'Spring', 2024, 65, 'SB-202', 'TTh 11:00-12:30'),
        ('BUS101', 'Business Fundamentals', 3, 4, 3, 'Fall', 2024, 70, 'BC-101', 'MW 3:00-4:30'),
        ('ENG201', 'Structural Analysis', 4, 5, 4, 'Spring', 2024, 35, 'EC-Lab1', 'TTh 2:00-3:30'),
        ('PSY101', 'Introduction to Psychology', 5, 6, 3, 'Fall', 2024, 90, 'SSH-301', 'MWF 10:00-11:00'),
        ('CS302', 'Cybersecurity', 1, 7, 3, 'Fall', 2024, 50, 'TA-Lab5', 'TTh 9:00-10:30')
    ]
    cursor.executemany('''INSERT INTO COURSES 
                         (course_code, course_name, dept_id, prof_id, credits, semester, year, max_students, room, schedule) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', courses_data)
    print("✓ Inserted 10 courses")
    
    students_data = [
        ('Alice Johnson', 'STU001', 'alice.johnson@student.college.edu', '555-2001', 1, 3, 3.85, '2022-08-15', '2026-05-15', '123 Main St', '2003-06-15'),
        ('Bob Smith', 'STU002', 'bob.smith@student.college.edu', '555-2002', 1, 2, 3.42, '2023-08-15', '2027-05-15', '456 Oak Ave', '2004-03-22'),
        ('Carol Davis', 'STU003', 'carol.davis@student.college.edu', '555-2003', 2, 4, 3.91, '2021-08-15', '2025-05-15', '789 Pine St', '2002-11-08'),
        ('David Wilson', 'STU004', 'david.wilson@student.college.edu', '555-2004', 3, 3, 3.67, '2022-08-15', '2026-05-15', '321 Elm Dr', '2003-09-14'),
        ('Emma Brown', 'STU005', 'emma.brown@student.college.edu', '555-2005', 4, 1, 3.23, '2024-08-15', '2028-05-15', '654 Maple Ln', '2005-01-30'),
        ('Frank Miller', 'STU006', 'frank.miller@student.college.edu', '555-2006', 1, 4, 3.78, '2021-08-15', '2025-05-15', '987 Cedar Rd', '2002-07-19'),
        ('Grace Lee', 'STU007', 'grace.lee@student.college.edu', '555-2007', 5, 2, 3.56, '2023-08-15', '2027-05-15', '147 Birch Way', '2004-12-03'),
        ('Henry Taylor', 'STU008', 'henry.taylor@student.college.edu', '555-2008', 2, 3, 3.89, '2022-08-15', '2026-05-15', '258 Spruce St', '2003-04-11'),
        ('Ivy Chen', 'STU009', 'ivy.chen@student.college.edu', '555-2009', 1, 1, 3.94, '2024-08-15', '2028-05-15', '369 Willow Ave', '2005-08-25'),
        ('Jack Anderson', 'STU010', 'jack.anderson@student.college.edu', '555-2010', 3, 4, 3.45, '2021-08-15', '2025-05-15', '741 Poplar Dr', '2002-10-17'),
        ('Kate Rodriguez', 'STU011', 'kate.rodriguez@student.college.edu', '555-2011', 1, 2, 3.71, '2023-08-15', '2027-05-15', '852 Ash Blvd', '2004-05-06'),
        ('Liam Thompson', 'STU012', 'liam.thompson@student.college.edu', '555-2012', 4, 3, 3.33, '2022-08-15', '2026-05-15', '963 Hickory Ct', '2003-02-28')
    ]
    cursor.executemany('''INSERT INTO STUDENTS 
                         (name, student_number, email, phone, major_dept_id, year_level, gpa, enrollment_date, graduation_date, address, date_of_birth) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', students_data)
    print("✓ Inserted 12 students")
    
    enrollments_data = [
        (1, 1, 'Fall', 2024, 'A', '2024-08-20', 92.5, 96.0, 'Completed'),
        (1, 2, 'Spring', 2024, 'A-', '2024-01-15', 88.7, 94.5, 'Completed'),
        (2, 1, 'Fall', 2024, 'B+', '2024-08-20', 85.2, 89.0, 'Active'),
        (2, 5, 'Fall', 2024, 'B', '2024-08-20', 82.1, 91.5, 'Active'),
        (3, 5, 'Fall', 2024, 'A+', '2024-08-20', 97.3, 98.5, 'Active'),
        (3, 6, 'Spring', 2024, 'A', '2024-01-15', 91.8, 95.0, 'Completed'),
        (4, 7, 'Fall', 2024, 'A-', '2024-08-20', 87.9, 92.0, 'Active'),
        (5, 8, 'Spring', 2024, 'C+', '2024-01-15', 78.5, 85.0, 'Completed'),
        (6, 3, 'Fall', 2024, 'A', '2024-08-20', 90.4, 97.5, 'Active'),
        (6, 4, 'Spring', 2024, 'A+', '2024-01-15', 95.6, 99.0, 'Completed'),
        (7, 9, 'Fall', 2024, 'B+', '2024-08-20', 86.3, 88.5, 'Active'),
        (8, 5, 'Fall', 2024, 'A', '2024-08-20', 93.1, 96.5, 'Active'),
        (9, 1, 'Fall', 2024, 'A+', '2024-08-20', 98.2, 99.5, 'Active'),
        (10, 7, 'Fall', 2024, 'B', '2024-08-20', 81.7, 87.0, 'Active'),
        (11, 2, 'Spring', 2024, 'A-', '2024-01-15', 89.4, 93.5, 'Completed'),
        (12, 8, 'Spring', 2024, 'B-', '2024-01-15', 79.8, 84.0, 'Completed')
    ]
    cursor.executemany('''INSERT INTO ENROLLMENTS 
                         (student_id, course_id, semester, year, grade, enrollment_date, final_score, attendance_percentage, status) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', enrollments_data)
    print("✓ Inserted 16 enrollments")
    
    connection.commit()
    
    print("\n" + "="*50)
    print("DATABASE CREATION COMPLETE!")
    print("="*50)
    
    print("\nTABLE RELATIONSHIPS:")
    print("DEPARTMENTS (1) ←→ (Many) PROFESSORS")
    print("DEPARTMENTS (1) ←→ (Many) COURSES")
    print("DEPARTMENTS (1) ←→ (Many) STUDENTS (major)")
    print("PROFESSORS (1) ←→ (Many) COURSES")
    print("STUDENTS (Many) ←→ (Many) COURSES (via ENROLLMENTS)")
    
    print("\nRECORD COUNTS:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  {table[0]}: {count} records")
    
    print("\nSAMPLE QUERIES YOU CAN RUN:")
    print("1. SELECT * FROM STUDENTS WHERE gpa > 3.5;")
    print("2. SELECT s.name, d.dept_name FROM STUDENTS s JOIN DEPARTMENTS d ON s.major_dept_id = d.dept_id;")
    print("3. SELECT c.course_name, p.name FROM COURSES c JOIN PROFESSORS p ON c.prof_id = p.prof_id;")
    print("4. SELECT s.name, c.course_name, e.grade FROM ENROLLMENTS e JOIN STUDENTS s ON e.student_id = s.student_id JOIN COURSES c ON e.course_id = c.course_id;")
    print("5. SELECT d.dept_name, COUNT(s.student_id) as student_count FROM DEPARTMENTS d LEFT JOIN STUDENTS s ON d.dept_id = s.major_dept_id GROUP BY d.dept_name;")
    
    connection.close()
    print(f"\nDatabase 'college.db' created successfully!")
    print("Location: Current directory")

if __name__ == "__main__":
    create_college_database()