# Generated by Django 4.2.1 on 2023-06-08 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='is_removed',
            field=models.BooleanField(default=False, verbose_name='Удалено?'),
        ),
    ]
