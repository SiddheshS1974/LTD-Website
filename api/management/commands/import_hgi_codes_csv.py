import csv
from django.core.management.base import BaseCommand, CommandError
from api.models import ValidHGICode


class Command(BaseCommand):
    help = 'Import valid HGI codes from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []

                if 'Code' not in fieldnames:
                    raise CommandError(
                        f'Column "Code" not found. Available columns: {", ".join(fieldnames)}'
                    )

                rows = []
                for row in reader:
                    code = str(row.get('Code', '')).strip()
                    if code:
                        rows.append({
                            'code': code,
                            'first_name': str(row.get('First Name', '')).strip(),
                            'last_name': str(row.get('Last Name', '')).strip(),
                            'upline_rmd_name': str(row.get('Upline Rmd', '')).strip(),
                        })

        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Could not read file: {e}')

        if not rows:
            self.stdout.write(self.style.WARNING('No codes found in file.'))
            return

        created = 0
        updated = 0
        for row in rows:
            obj, was_created = ValidHGICode.objects.get_or_create(code=row['code'])
            obj.first_name = row['first_name']
            obj.last_name = row['last_name']
            obj.upline_rmd_name = row['upline_rmd_name']
            obj.save()
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} new codes imported, {updated} existing codes updated.'
        ))
