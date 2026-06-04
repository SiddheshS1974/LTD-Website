from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_validhgicode_extra_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('drive_file_id', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
            ],
        ),
    ]
