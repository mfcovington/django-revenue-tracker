# Generated by Django 2.1.3 on 2020-03-02 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ngs_project_tracker', '0002_auto_20181213_2204'),
        ('revenue_tracker', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='project',
        ),
        migrations.AddField(
            model_name='transaction',
            name='projects',
            field=models.ManyToManyField(blank=True, related_name='transactions', to='ngs_project_tracker.Project'),
        ),
    ]