# Generated by Django 5.0.6 on 2024-06-02 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='description',
            field=models.TextField(blank=True, help_text='Describe yourself, your likes and dislikes...', max_length=2097152, null=True, verbose_name='Who I am'),
        ),
    ]