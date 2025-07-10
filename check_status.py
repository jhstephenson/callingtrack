#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callingtrack.settings')
django.setup()

from callings.models import Calling

print("Current calling statuses:")
callings = Calling.objects.all()[:10]  # Get first 10 callings
for c in callings:
    print(f'ID: {c.id}, Status: "{c.status}", Name: {c.name or "No name"}')

print(f"\nTotal callings: {Calling.objects.count()}")
print(f"Callings with LCR_UPDATED status: {Calling.objects.filter(status='LCR_UPDATED').count()}")
print(f"Callings without LCR_UPDATED status: {Calling.objects.exclude(status='LCR_UPDATED').count()}")
