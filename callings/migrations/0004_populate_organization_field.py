from django.db import migrations


def populate_organization_field(apps, schema_editor):
    """
    Populate the organization field in calling records based on position titles.
    Since the old position.organization relationship was removed, we need to 
    map positions to organizations based on typical Church organizational patterns.
    """
    Calling = apps.get_model('callings', 'Calling')
    Organization = apps.get_model('callings', 'Organization')
    
    # Create a mapping of position titles to likely organizations
    position_to_org_mapping = {
        # Bishopric
        'Bishop': 'Bishopric',
        'First Counselor': 'Bishopric',
        'Second Counselor': 'Bishopric',
        'Executive Secretary': 'Bishopric',
        'Ward Clerk': 'Bishopric',
        'Assistant Ward Clerk': 'Bishopric',
        'Financial Clerk': 'Bishopric',
        
        # Elders Quorum
        'Elders Quorum President': 'Elders Quorum',
        'Elders Quorum First Counselor': 'Elders Quorum',
        'Elders Quorum Second Counselor': 'Elders Quorum',
        'Elders Quorum Secretary': 'Elders Quorum',
        'Elders Quorum Instructor': 'Elders Quorum',
        'Ministering Coordinator': 'Elders Quorum',
        
        # Relief Society
        'Relief Society President': 'Relief Society',
        'Relief Society First Counselor': 'Relief Society',
        'Relief Society Second Counselor': 'Relief Society',
        'Relief Society Secretary': 'Relief Society',
        'Relief Society Instructor': 'Relief Society',
        'Relief Society Ministering Coordinator': 'Relief Society',
        
        # Young Men
        'Young Men President': 'Young Men',
        'Young Men First Counselor': 'Young Men',
        'Young Men Second Counselor': 'Young Men',
        'Young Men Secretary': 'Young Men',
        'Young Men Advisor': 'Young Men',
        
        # Young Women
        'Young Women President': 'Young Women',
        'Young Women First Counselor': 'Young Women',
        'Young Women Second Counselor': 'Young Women',
        'Young Women Secretary': 'Young Women',
        'Young Women Advisor': 'Young Women',
        
        # Primary
        'Primary President': 'Primary',
        'Primary First Counselor': 'Primary',
        'Primary Second Counselor': 'Primary',
        'Primary Secretary': 'Primary',
        'Primary Teacher': 'Primary',
        'Primary Chorister': 'Primary',
        
        # Sunday School
        'Sunday School President': 'Sunday School',
        'Sunday School First Counselor': 'Sunday School',
        'Sunday School Second Counselor': 'Sunday School',
        'Sunday School Secretary': 'Sunday School',
        'Sunday School Teacher': 'Sunday School',
        
        # Music
        'Ward Organist': 'Music',
        'Ward Chorister': 'Music',
        'Choir Director': 'Music',
        'Assistant Organist': 'Music',
        'Assistant Chorister': 'Music',
        
        # Missionaries
        'Ward Mission Leader': 'Missionaries',
        'Ward Missionary': 'Missionaries',
        'Assistant Ward Mission Leader': 'Missionaries',
        
        # Others
        'Family History Consultant': 'Family History',
        'Temple and Family History Consultant': 'Family History',
        'Indexing Director': 'Family History',
        'Activities Committee': 'Activities',
        'Activities Director': 'Activities',
        'Emergency Preparedness Coordinator': 'Emergency Preparedness',
        'Welfare Specialist': 'Welfare',
    }
    
    # Get all organizations
    organizations = {org.name: org for org in Organization.objects.all()}
    
    # Get all callings that need organization assignment
    callings_needing_org = Calling.objects.filter(organization__isnull=True)
    
    for calling in callings_needing_org:
        position_title = calling.position.title
        
        # Try to find a matching organization
        org_name = position_to_org_mapping.get(position_title)
        
        if org_name and org_name in organizations:
            calling.organization = organizations[org_name]
            calling.save()
            print(f"Assigned {position_title} to {org_name}")
        else:
            # If no specific mapping found, try to create a generic organization
            # or assign to a default one
            default_org_name = "General Ward"
            if default_org_name not in organizations:
                default_org = Organization.objects.create(
                    name=default_org_name,
                    description="General ward organization for positions not assigned to specific organizations"
                )
                organizations[default_org_name] = default_org
            
            calling.organization = organizations[default_org_name]
            calling.save()
            print(f"Assigned {position_title} to default organization: {default_org_name}")


def reverse_populate_organization_field(apps, schema_editor):
    """Reverse operation - set all organization fields to null"""
    Calling = apps.get_model('callings', 'Calling')
    Calling.objects.all().update(organization=None)


class Migration(migrations.Migration):

    dependencies = [
        ('callings', '0003_add_organization_to_calling'),
    ]

    operations = [
        migrations.RunPython(
            populate_organization_field,
            reverse_populate_organization_field,
        ),
    ]
