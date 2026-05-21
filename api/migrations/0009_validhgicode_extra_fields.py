from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_validhgicode'),
    ]

    operations = [
        migrations.AddField(
            model_name='validhgicode',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='validhgicode',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='validhgicode',
            name='upline_rmd_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
