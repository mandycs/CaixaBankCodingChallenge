# Generated by Django 5.1.2 on 2024-10-27 00:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='accountNumber',
            field=models.CharField(default='cc6d29', max_length=6, unique=True, verbose_name='Account Number'),
        ),
    ]
