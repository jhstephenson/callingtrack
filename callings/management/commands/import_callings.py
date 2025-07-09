import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from callings.models import Unit, Organization, Position, Member, Calling

class Command(BaseCommand):
    help = 'Import callings data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        # Create or get default units and organizations
        self.create_default_data()
        
        # Track created records
        stats = {
            'units_created': 0,
            'organizations_created': 0,
            'positions_created': 0,
            'members_created': 0,
            'callings_created': 0,
            'callings_updated': 0,
            'rows_processed': 0,
            'rows_skipped': 0
        }

        current_unit = None
        current_org = None
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            # Skip the first two rows (header and subheader)
            for _ in range(2):
                next(csvfile)
                
            # Read the actual header row
            header = next(csv.reader([next(csvfile)]))
            
            # Process the data rows
            for row in csv.reader(csvfile):
                stats['rows_processed'] += 1
                
                # Skip empty rows
                if not any(row):
                    stats['rows_skipped'] += 1
                    continue
                    
                # Clean up row data
                row = [cell.strip() for cell in row]
                
                # Update current unit if specified
                if row[0]:  # Unit column
                    current_unit = row[0]
                    current_org = None  # Reset org when unit changes
                
                # Update current organization if specified
                if row[1]:  # Organization column
                    current_org = row[1]
                
                # Skip if we don't have required fields
                if not current_unit or not current_org or not row[2]:  # Position is required
                    stats['rows_skipped'] += 1
                    continue
                
                try:
                    # Get or create unit
                    unit_name = current_unit
                    unit, created = Unit.objects.get_or_create(
                        name=unit_name,
                        defaults={'unit_type': self.get_unit_type(unit_name)}
                    )
                    if created:
                        stats['units_created'] += 1
                    
                    # Get or create organization
                    org_name = current_org
                    org, created = Organization.objects.get_or_create(
                        name=org_name
                    )
                    if created:
                        stats['organizations_created'] += 1
                    
                    # Get or create position
                    position_title = row[2]  # Position column
                    position, created = Position.objects.get_or_create(
                        title=position_title,
                        organization=org,
                        defaults={
                            'is_leadership': self.is_leadership_position(position_title)
                        }
                    )
                    if created:
                        stats['positions_created'] += 1
                    
                    # Process member being released (Currently Called column)
                    released_member_name = row[3] if len(row) > 3 and row[3] else None
                    if released_member_name:
                        released_member = self.get_or_create_member(released_member_name, unit)
                        if released_member is not None:
                            stats['members_created'] += 1
                        
                        # Mark existing calling as released
                        self.release_existing_calling(unit, position, released_member, stats)
                    
                    # Process member being called (Name column)
                    called_member_name = row[6] if len(row) > 6 and row[6] else None
                    if called_member_name:
                        home_unit_name = row[7] if len(row) > 7 and row[7] else None
                        home_unit = unit  # Default to current unit
                        
                        if home_unit_name:
                            home_unit, _ = Unit.objects.get_or_create(
                                name=home_unit_name,
                                defaults={'unit_type': self.get_unit_type(home_unit_name)}
                            )
                        
                        called_member = self.get_or_create_member(called_member_name, home_unit)
                        if called_member is not None:
                            stats['members_created'] += 1
                        
                        # Create new calling
                        self.create_new_calling(
                            unit=unit,
                            position=position,
                            member=called_member,
                            row=row,
                            stats=stats
                        )
                            
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error processing row {row}: {str(e)}"))
                    stats['rows_skipped'] += 1
        
        # Print import statistics
        self.stdout.write(self.style.SUCCESS('\nImport completed!'))
        self.stdout.write(f"Rows processed: {stats['rows_processed']}")
        self.stdout.write(f"Rows skipped: {stats['rows_skipped']}")
        self.stdout.write(f"Units created: {stats['units_created']}")
        self.stdout.write(f"Organizations created: {stats['organizations_created']}")
        self.stdout.write(f"Positions created: {stats['positions_created']}")
        self.stdout.write(f"Members created: {stats['members_created']}")
        self.stdout.write(f"Callings created: {stats['callings_created']}")
        self.stdout.write(f"Callings updated: {stats['callings_updated']}")
    
    def get_unit_type(self, unit_name):
        """Determine unit type based on name"""
        unit_name_lower = unit_name.lower()
        if 'stake' in unit_name_lower:
            return 'STAKE'
        elif 'branch' in unit_name_lower:
            return 'BRANCH'
        return 'WARD'
    
    def is_leadership_position(self, position_title):
        """Determine if a position is a leadership role"""
        leadership_terms = ['president', 'bishop', 'counselor', 'secretary', 'clerk', 'executive']
        return any(term in position_title.lower() for term in leadership_terms)
    
    def get_or_create_member(self, name, unit):
        """Get or create a member"""
        if not name:
            return None
            
        member, created = Member.objects.get_or_create(
            name=name,
            defaults={'home_unit': unit}
        )
        
        # Update home unit if it wasn't set
        if not created and not member.home_unit:
            member.home_unit = unit
            member.save()
            
        return member
    
    def release_existing_calling(self, unit, position, member, stats):
        """Mark existing calling as released"""
        if not all([unit, position, member]):
            return
            
        # Find and update existing active calling
        try:
            calling = Calling.objects.get(
                unit=unit,
                position=position,
                member=member,
                status='ACTIVE'
            )
            calling.status = 'RELEASED'
            calling.save()
            stats['callings_updated'] += 1
        except Calling.DoesNotExist:
            pass
    
    def parse_date(self, date_str):
        """Parse date from various formats"""
        if not date_str:
            return None
        try:
            # Try MM/DD/YYYY format first
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None
    
    def create_new_calling(self, unit, position, member, row, stats):
        """Create a new calling"""
        if not all([unit, position, member]):
            return
        
        # Get or create the called_by member (index 11 in the row)
        called_by_name = row[11] if len(row) > 11 and row[11] else None
        called_by = None
        if called_by_name:
            called_by = self.get_or_create_member(called_by_name, unit)
            if called_by is not None:
                stats['members_created'] += 1
        
        # Get or create the bishop_consulted_by member (index 9 in the row)
        bishop_consulted_by_name = row[9] if len(row) > 9 and row[9] else None
        bishop_consulted_by = None
        if bishop_consulted_by_name:
            bishop_consulted_by = self.get_or_create_member(bishop_consulted_by_name, unit)
            if bishop_consulted_by is not None:
                stats['members_created'] += 1
        
        # Get LCR updated status (last column)
        lcr_updated = False
        if row and len(row) > 15 and row[15].strip().upper() == 'TRUE':
            lcr_updated = True
        
        # Create the new calling
        calling, created = Calling.objects.get_or_create(
            unit=unit,
            position=position,
            member=member,
            status='ACTIVE',
            defaults={
                'called_by': called_by,
                'date_called': self.parse_date(row[5] if len(row) > 5 else None),  # Date column
                'date_sustained': self.parse_date(row[13] if len(row) > 13 else None),  # Sustained column
                'date_set_apart': self.parse_date(row[14] if len(row) > 14 else None),  # Set Apart column
                'presidency_approved': self.parse_date(row[8] if len(row) > 8 else None),  # Presidency Approved column
                'hc_approved': self.parse_date(row[10] if len(row) > 10 else None),  # HC Approved column
                'bishop_consulted_by': bishop_consulted_by,
                'lcr_updated': lcr_updated,
                'notes': f"Imported from CSV on {timezone.now().strftime('%Y-%m-%d')}"
            }
        )
        
        if created:
            stats['callings_created'] += 1
    
    def create_default_data(self):
        """Create any necessary default data"""
        # Create a default stake unit if it doesn't exist
        Unit.objects.get_or_create(
            name='Twin Falls Stake',
            defaults={'unit_type': 'STAKE'}
        )
