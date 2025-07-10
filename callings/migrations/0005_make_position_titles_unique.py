from django.db import migrations
from django.db.models import Count


def make_position_titles_unique(apps, schema_editor):
    """
    Make position titles unique by updating duplicates to be more specific
    """
    Position = apps.get_model('callings', 'Position')
    Calling = apps.get_model('callings', 'Calling')
    
    # Get all duplicate position titles
    duplicates = Position.objects.values('title').annotate(count=Count('id')).filter(count__gt=1)
    
    for duplicate in duplicates:
        title = duplicate['title']
        positions = Position.objects.filter(title=title)
        
        # For each duplicate position, try to make it unique based on associated callings
        for i, position in enumerate(positions):
            if i == 0:
                # Keep the first one as is
                continue
            
            # Get a sample calling for this position to determine organization context
            sample_calling = Calling.objects.filter(position=position).first()
            
            if sample_calling and sample_calling.organization:
                # Update the position title to include organization context
                new_title = f"{title} ({sample_calling.organization.name})"
                
                # Check if this new title already exists
                counter = 1
                original_new_title = new_title
                while Position.objects.filter(title=new_title).exists():
                    new_title = f"{original_new_title} #{counter}"
                    counter += 1
                
                position.title = new_title
                position.save()
                print(f"Updated position title: '{title}' -> '{new_title}'")
            else:
                # If no organization context, just add a number
                new_title = f"{title} #{i}"
                
                # Check if this new title already exists
                counter = 1
                original_new_title = new_title
                while Position.objects.filter(title=new_title).exists():
                    new_title = f"{title} #{counter}"
                    counter += 1
                
                position.title = new_title
                position.save()
                print(f"Updated position title: '{title}' -> '{new_title}'")


def reverse_make_position_titles_unique(apps, schema_editor):
    """
    Reverse operation - not easily reversible, so we'll pass
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('callings', '0004_populate_organization_field'),
    ]

    operations = [
        migrations.RunPython(
            make_position_titles_unique,
            reverse_make_position_titles_unique,
        ),
    ]
