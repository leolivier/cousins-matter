# Generated by Django 5.0.2 on 2024-02-25 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CousinsMatterParameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_content', models.TextField()),
                ('home_logo', models.ImageField(default='static/images/cousinsmatter.jpg', upload_to='')),
            ],
        ),
    ]
