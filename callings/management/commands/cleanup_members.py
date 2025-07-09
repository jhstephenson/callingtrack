from django.core.management.base import BaseCommand
from callings.models import Member
import re

class Command(BaseCommand):
    help = 'Clean up member entries that were incorrectly imported as dates'

    def handle(self, *args, **options):
        # Find members with names that look like dates (e.g., '06/29/2025')
        date_pattern = re.compile(r'^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*$')
        
        # Find all members with date-like names
        members_to_delete = []
        for member in Member.objects.all():
            if date_pattern.match(member.name):
                members_to_delete.append(member)
        
        # Delete the problematic members
        if members_to_delete:
            self.stdout.write(f"Found {len(members_to_delete)} members with date-like names to be deleted:")
            for member in members_to_delete:
                self.stdout.write(f"- {member.name} (ID: {member.id})")
            
            # Delete the members
            count, _ = Member.objects.filter(
                id__in=[m.id for m in members_to_delete]
            ).delete()
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} members"))
        else:
            self.stdout.write("No members with date-like names found")
