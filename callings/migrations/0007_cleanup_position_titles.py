from django.db import migrations
import re


def cleanup_position_titles(apps, schema_editor):
    """
    Clean up position titles by removing organization context and numbered suffixes
    that were added during the decoupling migration.
    """
    Position = apps.get_model('callings', 'Position')
    
    # Pattern to match titles with organization context in parentheses
    # Example: "1st Counselor (General Ward)" or "Executive Secretary (Bishopric) #1"
    pattern = r'^(.+?)\s*\([^)]+\)(?:\s*#\d+)?$'
    
    for position in Position.objects.all():
        original_title = position.title
        match = re.match(pattern, original_title)
        
        if match:
            # Extract the base title without organization context
            base_title = match.group(1).strip()
            
            # Check if this base title already exists
            if Position.objects.filter(title=base_title).exists():
                # If it exists, we need to keep it unique but make it cleaner
                # We'll use just a number suffix without organization context
                counter = 1
                new_title = f"{base_title} {counter}"
                while Position.objects.filter(title=new_title).exists():
                    counter += 1
                    new_title = f"{base_title} {counter}"
                
                position.title = new_title
                position.save()
                print(f"Updated: '{original_title}' -> '{new_title}'")
            else:
                # No conflict, use the clean base title
                position.title = base_title
                position.save()
                print(f"Cleaned: '{original_title}' -> '{base_title}'")


def reverse_cleanup_position_titles(apps, schema_editor):
    """
    Reverse operation - not easily reversible, so we'll pass
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('callings', '0006_finalize_decoupled_models'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_position_titles,
            reverse_cleanup_position_titles,
        ),
    ]
