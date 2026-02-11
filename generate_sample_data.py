"""
Sample Data Generator for Student Results System

Run this script to populate the database with sample data for testing.

Usage:
    python manage.py shell < generate_sample_data.py
"""

from datetime import datetime, timedelta
from results.models import Student, StudentMetadata, Course, Result
import random

print("Generating sample data...")

# Clear existing data (optional - comment out if you want to keep existing data)
# Result.objects.all().delete()
# Course.objects.all().delete()
# StudentMetadata.objects.all().delete()
# Student.objects.all().delete()

# Sample data
departments = ['Computer Science', 'Information Science', 'Electronics', 'Mechanical', 'Civil']
admission_routes = ['COMEDK', 'KCET', 'MANAGEMENT']
grades = ['A+', 'A', 'B+', 'B', 'C', 'D', 'F']

# Generate courses for Semester 1-4
courses_data = [
    # Semester 1
    ('21CS101', 'Introduction to Programming', 1, 4),
    ('21CS102', 'Mathematics-I', 1, 4),
    ('21CS103', 'Physics', 1, 4),
    ('21CS104', 'English Communication', 1, 3),
    ('21CS105', 'Engineering Graphics', 1, 3),
    
    # Semester 2
    ('21CS201', 'Data Structures', 2, 4),
    ('21CS202', 'Mathematics-II', 2, 4),
    ('21CS203', 'Digital Electronics', 2, 4),
    ('21CS204', 'Computer Organization', 2, 3),
    ('21CS205', 'Discrete Mathematics', 2, 3),
    
    # Semester 3
    ('21CS301', 'Database Management Systems', 3, 4),
    ('21CS302', 'Operating Systems', 3, 4),
    ('21CS303', 'Computer Networks', 3, 4),
    ('21CS304', 'Object Oriented Programming', 3, 3),
    ('21CS305', 'Theory of Computation', 3, 3),
    
    # Semester 4
    ('21CS401', 'Web Technologies', 4, 4),
    ('21CS402', 'Software Engineering', 4, 4),
    ('21CS403', 'Microprocessors', 4, 4),
    ('21CS404', 'Algorithm Design', 4, 3),
    ('21CS405', 'Compiler Design', 4, 3),
]

print("Creating courses...")
for code, title, sem, credits in courses_data:
    course, created = Course.objects.get_or_create(
        course_code=code,
        defaults={
            'course_title': title,
            'semester': sem,
            'credits': credits
        }
    )
    if created:
        print(f"  Created course: {code} - {title}")

# Generate 50 sample students
print("\nCreating students...")
for i in range(1, 51):
    # Generate USN (format: 1XX21CS0XX)
    usn = f"1XX21CS{str(i).zfill(3)}"
    
    # Random name
    first_names = ['Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Aryan', 'Reyansh', 
                   'Ayush', 'Krishna', 'Pranav', 'Ananya', 'Diya', 'Aarohi', 'Pari', 'Anika',
                   'Navya', 'Angel', 'Anvi', 'Saanvi', 'Ira', 'Myra', 'Sara', 'Riya']
    last_names = ['Kumar', 'Sharma', 'Verma', 'Singh', 'Patel', 'Reddy', 'Gupta', 'Jain',
                  'Agarwal', 'Rao', 'Nair', 'Iyer', 'Menon', 'Pillai', 'Das', 'Bose']
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    department = random.choice(departments)
    
    # Create student
    student, created = Student.objects.get_or_create(
        usn=usn,
        defaults={
            'name': name,
            'department': department,
            'semester': random.randint(1, 4)
        }
    )
    
    if created:
        print(f"  Created student: {usn} - {name}")
        
        # Create metadata
        dob = datetime(2004, 1, 1) + timedelta(days=random.randint(0, 730))
        admission_route = random.choice(admission_routes)
        
        StudentMetadata.objects.create(
            student=student,
            dob=dob.date(),
            admission_route=admission_route
        )
        
        # Generate results for semesters 1-3
        for semester in range(1, 4):
            semester_courses = Course.objects.filter(semester=semester)
            
            for course in semester_courses:
                # Generate random marks (20-50 for CIE)
                marks = random.randint(20, 50)
                
                # Determine grade in words
                if marks >= 45:
                    marks_words = random.choice(['Excellent', 'Outstanding'])
                elif marks >= 40:
                    marks_words = random.choice(['Very Good', 'Good'])
                elif marks >= 35:
                    marks_words = 'Average'
                else:
                    marks_words = 'Below Average'
                
                Result.objects.create(
                    student=student,
                    course=course,
                    final_cie_marks=marks,
                    marks_in_words=marks_words,
                    semester=semester,
                    academic_year='2023-24',
                    scheme='2021 Scheme'
                )

print("\n" + "="*50)
print("Sample data generation complete!")
print("="*50)

# Print summary
print(f"\nSummary:")
print(f"  Students: {Student.objects.count()}")
print(f"  Courses: {Course.objects.count()}")
print(f"  Results: {Result.objects.count()}")
print(f"  Metadata records: {StudentMetadata.objects.count()}")

print("\nSample credentials for testing:")
print("  USN: 1XX21CS001")
print("  DOB: (check admin panel for exact date)")
print("  Semester: 1, 2, or 3")

print("\nYou can now:")
print("  1. Visit the home page and query results")
print("  2. Login to admin panel with superuser credentials")
print("  3. View analytics and statistics")
print("  4. Test PDF download functionality")

