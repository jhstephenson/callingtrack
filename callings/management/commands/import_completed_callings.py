import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from callings.models import Unit, Organization, Position, Member, Calling

class Command(BaseCommand):
    help = 'Import completed callings from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the completed callings CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            raise CommandError(f'File "{csv_file}" does not exist')

        stats = {
            'rows_processed': 0,
            'rows_skipped': 0,
            'units_created': 0,
            'organizations_created': 0,
            'positions_created': 0,
            'members_created': 0,
            'callings_created': 0,
            'callings_updated': 0,
        }

        # Track current unit and org for hierarchical data
        current_unit = None
        current_org = None

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = []
            
            # Skip the first two rows (title and empty row)
            next(reader)  # Title row
            next(reader)  # Empty row
            
            # Get headers from the third row
            headers = [h.strip() for h in next(reader)]
            
            for i, row in enumerate(reader, 1):
                if not any(row):  # Skip empty rows
                    continue
                
                try:
                    # Convert empty strings to None
                    row = [cell.strip() if cell.strip() else None for cell in row]
                    
                    # Update current unit if this row has one
                    if row[0]:  # Unit column
                        current_unit = row[0].strip()
                    
                    # Update current org if this row has one
                    if row[1]:  # Organization column
                        current_org = row[1].strip()
                    
                    if not current_unit or not current_org:
                        stats['rows_skipped'] += 1
                        continue
                    
                    # Get or create Unit
                    unit_type = 'STAKE' if 'stake' in current_unit.lower() else 'WARD' if 'ward' in current_unit.lower() else 'BRANCH'
                    unit, created = Unit.objects.get_or_create(
                        name=current_unit,
                        defaults={'unit_type': unit_type}
                    )
                    if created:
                        stats['units_created'] += 1
                    
                    # Get or create Organization
                    org, created = Organization.objects.get_or_create(name=current_org)
                    if created:
                        stats['organizations_created'] += 1
                    
                    # Get or create Position
                    position_title = row[2]  # Position column
                    if not position_title:
                        stats['rows_skipped'] += 1
                        continue
                        
                    position, created = Position.objects.get_or_create(
                        title=position_title,
                        organization=org,
                        defaults={'is_leadership': any(role in position_title.lower() for role in ['president', 'bishop', 'counselor', 'secretary', 'clerk'])}
                    )
                    if created:
                        stats['positions_created'] += 1
                    
                    # Get or create Member (Currently Called)
                    member_name = row[3]  # Currently Called column
                    
                    # Skip rows with empty or invalid member names
                    if not member_name or member_name.lower().strip() in ['', 'n/a', 'vacant']:
                        stats['rows_skipped'] += 1
                        self.stdout.write(f"Skipping row {i}: No member name provided")
                        continue
                    
                    # Clean up the member name
                    member_name = member_name.strip()
                    
                    # Skip if the name looks like a date (e.g., '06/29/2025')
                    if any(c.isdigit() for c in member_name) and any(c in member_name for c in ['/', '-']):
                        stats['rows_skipped'] += 1
                        self.stdout.write(f"Skipping row {i}: Invalid member name (appears to be a date): {member_name}")
                        continue
                    
                    try:
                        member, created = Member.objects.get_or_create(
                            name=member_name,
                            defaults={'home_unit': unit}
                        )
                    except Exception as e:
                        self.stderr.write(f"Error creating/updating member '{member_name}': {e}")
                        stats['rows_skipped'] += 1
                        continue
                    if created:
                        stats['members_created'] += 1
                    
                    # Parse dates
                    def parse_date(date_str):
                        if not date_str:
                            return None
                        try:
                            return datetime.strptime(date_str, '%m/%d/%Y').date()
                        except (ValueError, TypeError):
                            try:
                                return datetime.strptime(date_str, '%m-%d-%Y').date()
                            except (ValueError, TypeError):
                                return None
                    
                    # Create or update Calling
                    calling_data = {
                        'unit': unit,
                        'position': position,
                        'member': member,
                        'status': 'COMPLETED',  # Mark as completed
                        'calling_status': 'RELEASED',  # Mark as released
                        'date_called': parse_date(row[12]),  # Date Called
                        'date_sustained': parse_date(row[13]),  # Sustained
                        'date_set_apart': parse_date(row[14]),  # Set Apart
                        'presidency_approved': parse_date(row[8]),  # Date Approved
                        'hc_approved': parse_date(row[10]),  # Date Approved by HC
                        'lcr_updated': row[15].lower() == 'true' if row[15] else False,  # LCR Updated
                        'notes': f"Imported from completed callings. Released by: {row[4] or 'N/A'}",
                    }
                    
                    # Handle called_by if available
                    called_by_name = row[11]  # To Be Called By
                    if called_by_name and called_by_name.lower() not in ['n/a', '']:
                        called_by, _ = Member.objects.get_or_create(
                            name=called_by_name,
                            defaults={'home_unit': unit}
                        )
                        calling_data['called_by'] = called_by
                    
                    # Handle bishop_consulted_by if available
                    bishop_consulted = row[9]  # Bishop To Be Consulted By
                    if bishop_consulted and bishop_consulted.lower() not in ['n/a', '']:
                        bishop, _ = Member.objects.get_or_create(
                            name=bishop_consulted,
                            defaults={'home_unit': unit}
                        )
                        calling_data['bishop_consulted_by'] = bishop
                    
                    # Create or update the calling
                    calling, created = Calling.objects.update_or_create(
                        member=member,
                        position=position,
                        unit=unit,
                        defaults=calling_data
                    )
                    
                    if created:
                        stats['callings_created'] += 1
                    else:
                        stats['callings_updated'] += 1
                    
                    stats['rows_processed'] += 1
                    
                    if stats['rows_processed'] % 10 == 0:
                        self.stdout.write(f"Processed {stats['rows_processed']} rows...")
                        
                except Exception as e:
                    self.stderr.write(f"Error processing row {i}: {e}")
                    stats['rows_skipped'] += 1
                    continue
        
        # Print summary
        self.stdout.write("\nImport completed!")
        self.stdout.write(f"Rows processed: {stats['rows_processed']}")
        self.stdout.write(f"Rows skipped: {stats['rows_skipped']}")
        self.stdout.write(f"Units created: {stats['units_created']}")
        self.stdout.write(f"Organizations created: {stats['organizations_created']}")
        self.stdout.write(f"Positions created: {stats['positions_created']}")
        self.stdout.write(f"Members created: {stats['members_created']}")
        self.stdout.write(f"Callings created: {stats['callings_created']}")
        self.stdout.write(f"Callings updated: {stats['callings_updated']}")
