# Generated by Django 5.1.2 on 2024-10-27 00:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_customuser_accountnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='accountNumber',
            field=models.CharField(default='deac9f', max_length=6, unique=True, verbose_name='Account Number'),
        ),
    ]
