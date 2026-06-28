from django.db import migrations


def backfill_rmd_role(apps, schema_editor):
    CustomUser = apps.get_model('api', 'CustomUser')
    updated = CustomUser.objects.filter(is_rmd_member=True).exclude(role='RMD').update(
        role='RMD',
        is_rmd=True,
    )
    print(f"  Backfilled RMD role for {updated} user(s).")


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_remove_upline_rmd_hgi_code'),
    ]

    operations = [
        migrations.RunPython(backfill_rmd_role, migrations.RunPython.noop),
    ]
