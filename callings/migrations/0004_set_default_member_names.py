from django.db import migrations

def set_default_member_names(apps, schema_editor):
    Member = apps.get_model('callings', 'Member')
    # Update existing members with empty required fields
    Member.objects.filter(first_name__isnull=True).update(first_name='Unknown')
    Member.objects.filter(last_name__isnull=True).update(last_name='Member')

class Migration(migrations.Migration):
    dependencies = [
        ('callings', '0003_calling_calling_status_alter_calling_status'),
    ]

    operations = [
        migrations.RunPython(set_default_member_names, reverse_code=migrations.RunPython.noop),
    ]
