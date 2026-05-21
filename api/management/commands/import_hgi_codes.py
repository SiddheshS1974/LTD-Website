import openpyxl
from django.core.management.base import BaseCommand, CommandError
from api.models import ValidHGICode


class Command(BaseCommand):
    help = 'Import valid HGI codes from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file (.xlsx)')
        parser.add_argument(
            '--column',
            type=int,
            default=1,
            help='Column number containing HGI codes (default: 1)',
        )
        parser.add_argument(
            '--sheet',
            type=int,
            default=1,
            help='Sheet number to read from (default: 1)',
        )
        parser.add_argument(
            '--skip-header',
            action='store_true',
            help='Skip the first row (header row)',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        col_index = options['column'] - 1  # Convert to 0-based
        sheet_index = options['sheet'] - 1
        skip_header = options['skip_header']

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Could not open file: {e}')

        sheet = wb.worksheets[sheet_index]
        rows = list(sheet.iter_rows(values_only=True))

        if skip_header:
            rows = rows[1:]

        codes = set()
        for row in rows:
            if col_index < len(row) and row[col_index] is not None:
                code = str(row[col_index]).strip()
                if code:
                    codes.add(code)

        wb.close()

        if not codes:
            self.stdout.write(self.style.WARNING('No codes found in file.'))
            return

        created = 0
        skipped = 0
        for code in codes:
            _, was_created = ValidHGICode.objects.get_or_create(code=code)
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} new codes imported, {skipped} already existed.'
        ))
