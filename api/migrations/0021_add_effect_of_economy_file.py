from django.db import migrations


def add_file(apps, schema_editor):
    ProtectedFile = apps.get_model('api', 'ProtectedFile')
    ProtectedFile.objects.get_or_create(
        drive_file_id="1_SKMpgtaEL4wI2tJ2RHn_WLEw-bxeyIm",
        defaults={"slug": "effect-of-economy", "title": "Effect of Economy"},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_fix_stale_drive_file_ids'),
    ]

    operations = [
        migrations.RunPython(add_file, migrations.RunPython.noop),
    ]
