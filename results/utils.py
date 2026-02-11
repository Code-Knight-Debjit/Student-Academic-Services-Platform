"""
Utility functions for Excel/CSV data processing.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from django.db import transaction
from .models import Student, StudentMetadata, Course, Result, UploadHistory


def detect_column(df, keywords):
    """
    Detect column name using case-insensitive keyword matching.
    
    Args:
        df: pandas DataFrame
        keywords: list of keywords to search for
    
    Returns:
        Column name if found, None otherwise
    """
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in keywords:
            if keyword.lower() in col_lower:
                return col
    return None


def process_results_excel(file_path, user=None):
    try:
        # ---------- NEW: Read raw file to extract course title ----------
        raw_df = pd.read_excel(file_path, header=None)

        course_title_detected = None
        for i in range(7):  # first 7 garbage rows
            row_text = " ".join(raw_df.iloc[i].astype(str).tolist()).strip()
            if "introduction" in row_text.lower() or "course" in row_text.lower():
                course_title_detected = row_text
                break

        if course_title_detected:
            # Clean title
            course_title_detected = course_title_detected.replace("\n", " ")
            course_title_detected = " ".join(course_title_detected.split())
        else:
            course_title_detected = "UNKNOWN COURSE"
        # ---------- END NEW ----------

        # Read Excel file, skipping first 7 rows
        df = pd.read_excel(file_path, skiprows=7)

        # ---------- NEW: Clean column names ----------
        df.columns = df.columns.str.strip()
        # ---------- END NEW ----------

        # ---------- NEW: Add course column ----------
        df['course'] = course_title_detected
        # ---------- END NEW ----------

        # Detect columns using keywords
        usn_col = detect_column(df, ['usn', 'USN'])
        name_col = detect_column(df, ['name', 'Name'])
        cie_col = detect_column(df, ['Final CIE', 'CIE', 'Final CIE Marks'])
        course_col = detect_column(df, ['course', 'subject'])  # now exists
        words_col = detect_column(df, ['words', 'in words', 'Marks In Words'])

        if not all([usn_col, name_col, course_col]):
            raise ValueError("Missing required columns (USN, Name, Course)")

        stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    usn = str(row[usn_col]).strip().upper() if pd.notna(row[usn_col]) else None
                    name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                    course_title = str(row[course_col]).strip() if pd.notna(row[course_col]) else None

                    if not usn or not name or not course_title or len(usn) != 10:
                        stats['skipped'] += 1
                        continue

                    if not usn.isalnum() or len(usn) != 10:
                        stats['skipped'] += 1
                        continue

                    stats['processed'] += 1

                    student, created = Student.objects.update_or_create(
                        usn=usn,
                        defaults={'name': name}
                    )

                    # FIXED metadata check
                    try:
                        student.metadata
                    except StudentMetadata.DoesNotExist:
                        StudentMetadata.objects.create(
                            student=student,
                            dob=datetime(2006, 1, 1).date()
                        )

                    course_code = course_title[:20].upper().replace(' ', '_')

                    course, _ = Course.objects.update_or_create(
                        course_code=course_code,
                        defaults={
                            'course_title': course_title,
                            'semester': 1
                        }
                    )

                    cie_marks = None
                    if cie_col and pd.notna(row[cie_col]):
                        try:
                            cie_marks = float(row[cie_col])
                        except (ValueError, TypeError):
                            cie_marks = None

                    marks_words = None
                    if words_col and pd.notna(row[words_col]):
                        marks_words = str(row[words_col]).strip()

                    result, result_created = Result.objects.update_or_create(
                        student=student,
                        course=course,
                        defaults={
                            'final_cie_marks': cie_marks,
                            'marks_in_words': marks_words,
                            'semester': 1
                        }
                    )

                    if result_created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1

                except Exception as e:
                    stats['errors'].append(f"Row {idx + 9}: {str(e)}")
                    stats['skipped'] += 1

        UploadHistory.objects.create(
            upload_type='RESULTS',
            file_name=file_path.split('/')[-1],
            uploaded_by=user,
            records_processed=stats['processed'],
            records_created=stats['created'],
            records_updated=stats['updated'],
            records_skipped=stats['skipped'],
            success=True
        )

        return stats

    except Exception as e:
        if user:
            UploadHistory.objects.create(
                upload_type='RESULTS',
                file_name=file_path.split('/')[-1],
                uploaded_by=user,
                success=False,
                error_message=str(e)
            )
        raise e


def process_metadata_excel(file_path, user=None):
    """
    Process student metadata Excel file.
    
    Expected columns:
    - USN
    - DOB
    - Admission Route (optional)
    
    Returns:
        Dictionary with processing statistics
    """
    try:
        df = pd.read_excel(file_path)
        
        # Detect columns
        usn_col = detect_column(df, ['usn'])
        dob_col = detect_column(df, ['dob', 'date of birth', 'birth'])
        route_col = detect_column(df, ['admission', 'route', 'quota'])
        
        if not usn_col or not dob_col:
            raise ValueError("Missing required columns (USN, DOB)")
        
        stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    usn = str(row[usn_col]).strip().upper() if pd.notna(row[usn_col]) else None
                    
                    if not usn or len(usn) != 10 or not usn.isalnum():
                        stats['skipped'] += 1
                        continue
                    
                    # Parse DOB
                    dob_value = row[dob_col]
                    if pd.isna(dob_value):
                        stats['skipped'] += 1
                        continue
                    
                    if isinstance(dob_value, str):
                        dob = pd.to_datetime(dob_value, errors='coerce').date()
                    else:
                        dob = pd.to_datetime(dob_value).date()
                    
                    if not dob:
                        stats['skipped'] += 1
                        continue
                    
                    stats['processed'] += 1
                    
                    # Get or create student
                    student, _ = Student.objects.get_or_create(
                        usn=usn,
                        defaults={'name': 'Unknown'}
                    )
                    
                    # Parse admission route
                    admission_route = None
                    if route_col and pd.notna(row[route_col]):
                        route_str = str(row[route_col]).strip().upper()
                        if 'COMEDK' in route_str:
                            admission_route = 'COMEDK'
                        elif 'KCET' in route_str:
                            admission_route = 'KCET'
                        elif 'MANAGEMENT' in route_str or 'MGMT' in route_str:
                            admission_route = 'MANAGEMENT'
                    
                    # Create or update metadata (replace existing)
                    metadata, created = StudentMetadata.objects.update_or_create(
                        student=student,
                        defaults={
                            'dob': dob,
                            'admission_route': admission_route
                        }
                    )
                    
                    if created:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                        
                except Exception as e:
                    stats['errors'].append(f"Row {idx + 2}: {str(e)}")
                    stats['skipped'] += 1
        
        # Log upload history
        UploadHistory.objects.create(
            upload_type='METADATA',
            file_name=file_path.split('/')[-1],
            uploaded_by=user,
            records_processed=stats['processed'],
            records_created=stats['created'],
            records_updated=stats['updated'],
            records_skipped=stats['skipped'],
            success=True
        )
        
        return stats
        
    except Exception as e:
        if user:
            UploadHistory.objects.create(
                upload_type='METADATA',
                file_name=file_path.split('/')[-1],
                uploaded_by=user,
                success=False,
                error_message=str(e)
            )
        raise e

