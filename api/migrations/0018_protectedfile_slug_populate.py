from django.db import migrations, models

INITIAL_FILES = [
    ("bop-presentation",              "1rfoaufbnE5_UhyxBcYdy3EGaprMGgk1t", "BOP US Presentation"),
    ("financial-literacy-presentation","1Wx3ZsSr8uLdt55ZWYkCeByGIzh-6rcdk", "Financial Literacy & Estate Planning Presentation"),
    ("retirement-calculations",        "17TJ1jJezCmUrxpaEemOCl4TYILCYeXtb", "Retirement Calculations"),
    ("fna-excel-sheet",                "1enc58SIxXWacwrp5N4pVg7xoD0GgFMOC", "Financial Needs Analysis Excel Sheet Template"),
    ("fls-presentation",               "1M4FXBYugvdutO-9yqUSYpKuPJUvGp0CX", "Financial Lifestyle Strategy Client Presentation"),
    ("saving-vs-investing",            "1P4ORFiviz6WdJZb8qP7F7iCx5VZGD--w", "Saving vs Investing"),
    ("tax-401k-overfunding",           "1P4d56XfCpxhVMtFX9iWExYUvADseK0Qg", "Tax Calculation for 401K Overfunding"),
    ("comparisons",                    "1hDQ1aWfTQEgyUxVpujTc8BrDkgVFpANZ", "Comparisons"),
    ("estate-planning-intro",          "1Q4N5PsyNG6mx_w6Tnx3k6hhrE9au1siY", "Introduction to Estate Planning"),
    ("estate-planning-roles",          "1beBOGXJSltAtuQlRnIQpI5TX7HKZqC4J", "Estate Planning Roles"),
    ("license-registration-process",   "1ft1bISGL3u3TcmMT13aBNCrbZZt4B_p0", "License Registration Process"),
    ("non-resident-license",           "1H6Pl53OcIPCb4_HIODZL4wYaZ7M9a5LZ", "Applying for Non-Resident License"),
    ("netlaw-form",                    "1R01mYpYYb0aCjMt8YqCTxrZLLoMx6Oli", "Form for Netlaw Doc Preparation Video Access"),
    ("ltd-videos-access",              "1Pdk9pKLHO7jekxLUHtJSAxBdNDzDKP0z", "Getting Access to LTD Videos"),
    ("na-application-forms",           "1NsPHHL9fLUfA2KEBu_Xq-hxNl83FJTuE", "Getting Forms for Applications — North American"),
    ("commission-calculations",        "1Pk1b-SuBXeEg2qqmdzD5rhBlqgIBJlys", "Commission Calculations"),
    ("register-north-american",        "1Jz6rm6YcGg2n8QjutiicpyyVIQZi2OK0", "North American — Register Client Account"),
    ("register-athene",                "1P1lh80cUEKNmzm4KkuMrSjMPQcdpbha5", "Athene — Register Client Account"),
    ("register-fg",                    "18bNGIXP_6h2ttRMRJVJ213P70N1mzH22", "F&G — Register Client Account"),
    ("setup-surelc",                   "15RkXZUp7YSEboBWv8Io59j0-Q47X1fcB", "Setting up SureLC"),
    ("athene-product-training",        "1LN_fkF4Z_0fkJl0kqQarZk7t03iVBoRZ", "Athene Product Trainings"),
    ("annuity-suitability",            "1LQO6rIvOxiPgBkaw5ftt4LLS8ZL0I5FG", "Best Interest Annuity Suitability"),
    ("na-iul-training",                "1LRT7kUOVGNP7fE0rkME8l-v_x48Z9AU4", "North American IUL Product Training"),
    ("nationwide-annexus-training",    "1LXcKjUkLB2yk-NVxAFN_nVU0jGvSP_rK", "Nationwide-Annexus Annuity Product Training"),
]


def populate_files(apps, schema_editor):
    ProtectedFile = apps.get_model('api', 'ProtectedFile')
    for slug, drive_id, title in INITIAL_FILES:
        obj, _ = ProtectedFile.objects.get_or_create(drive_file_id=drive_id)
        if not obj.slug:
            obj.slug = slug
            if not obj.title:
                obj.title = title
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_customuser_granted_pages'),
    ]

    operations = [
        migrations.AddField(
            model_name='protectedfile',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.RunPython(populate_files, migrations.RunPython.noop),
    ]
