# Generated by Django 4.2.1 on 2023-05-31 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Road',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_public', models.BooleanField(default=False, verbose_name='Опубликовано?')),
                ('title', models.CharField(default='Дорога', max_length=150, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Дорога',
                'verbose_name_plural': 'Дороги',
            },
        ),
    ]
