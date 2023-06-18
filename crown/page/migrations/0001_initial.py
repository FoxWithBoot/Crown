# Generated by Django 4.2.1 on 2023-06-17 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_public', models.BooleanField(default=False, verbose_name='Опубликовано?')),
                ('is_removed', models.BooleanField(default=False, verbose_name='Удалено?')),
                ('title', models.CharField(default='Страница', max_length=150, verbose_name='Название')),
                ('floor', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Индекс в списке подстраниц')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
            ],
            options={
                'verbose_name': 'Страница',
                'verbose_name_plural': 'Страницы',
            },
        ),
    ]
