from django.db import migrations

FIXES = [
    ("bop-presentation",               "1eDer8Nb5eBRkgus1Z8mhj4x4Z26e_R-R"),
    ("financial-literacy-presentation","1hJHx7Mn0AfxrNdv-RMv1nyMdsivsyYR3"),
    ("retirement-calculations",        "1j8d2JwiKxMs2cM31EkCvtxAc5OVsTDX2"),
    ("fna-excel-sheet",                "156w6Eta82FLXXDfAcP5iDaOT8c5x_r52"),
    ("fls-presentation",               "13rz6s4XfBZptxV-CqCTMBLcqFtVQO0Uw"),
    ("saving-vs-investing",            "1lyIjaIJywQ5ysVXwc91M7E3bgL9nMAb5"),
    ("tax-401k-overfunding",           "1iJFXdqrRG2tpH13dfFLhG_Jac-uTbiCC"),
    ("non-resident-license",           "1tumLWblhhH1SzlaZrNME1ScwFNZjWGLP"),
    ("netlaw-form",                    "1Toghc2ySh4PbEuXkB0dx20alVCcbw2TE"),
    ("ltd-videos-access",              "1s35v1A46cJspxq-AcVLQGEAKFTES4kFv"),
]


def fix_ids(apps, schema_editor):
    ProtectedFile = apps.get_model('api', 'ProtectedFile')
    for slug, new_drive_id in FIXES:
        ProtectedFile.objects.filter(slug=slug).update(drive_file_id=new_drive_id)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_customuser_certifications_alter_customuser_role'),
    ]

    operations = [
        migrations.RunPython(fix_ids, migrations.RunPython.noop),
    ]
