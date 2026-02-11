"""
Forms for Student Results System.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Student, Result, Course
import requests
from django.conf import settings


class ResultQueryForm(forms.Form):
    """Form for querying student results."""
    usn = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'placeholder': 'Enter USN (10 characters)',
            'autocomplete': 'off'
        })
    )
    dob = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all'
        })
    )
    semester = forms.IntegerField(
        min_value=1,
        max_value=8,
        widget=forms.Select(
            choices=[(i, f'Semester {i}') for i in range(1, 9)],
            attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all'
            }
        )
    )
    recaptcha_response = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean_usn(self):
        usn = self.cleaned_data['usn'].strip().upper()
        if len(usn) != 10:
            raise ValidationError('USN must be exactly 10 characters')
        if not usn.isalnum():
            raise ValidationError('USN must be alphanumeric')
        return usn

    def verify_recaptcha(self, recaptcha_response):
        """Verify Google reCAPTCHA response."""
        if not settings.RECAPTCHA_SECRET_KEY:
            return True  # Skip verification if not configured
        
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                },
                timeout=5
            )
            result = response.json()
            return result.get('success', False)
        except:
            return False  # Fail closed


class BulkUploadForm(forms.Form):
    """Form for bulk Excel/CSV upload."""
    UPLOAD_TYPES = [
        ('results', 'Results Data'),
        ('metadata', 'Student Metadata'),
    ]
    
    upload_type = forms.ChoiceField(
        choices=UPLOAD_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all'
        })
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'accept': '.xlsx,.xls,.csv'
        })
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith(('.xlsx', '.xls', '.csv')):
            raise ValidationError('Only Excel (.xlsx, .xls) and CSV files are allowed')
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError('File size must be under 10MB')
        return file


class ResultEditForm(forms.ModelForm):
    """Form for editing individual result marks."""
    class Meta:
        model = Result
        fields = ['final_cie_marks', 'marks_in_words', 'academic_year', 'scheme']
        widgets = {
            'final_cie_marks': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
                'step': '0.01'
            }),
            'marks_in_words': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., 2023-24'
            }),
            'scheme': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
        }


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with Tailwind styling."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'placeholder': 'Username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )
