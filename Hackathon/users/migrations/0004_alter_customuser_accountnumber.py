# Generated by Django 5.1.2 on 2024-10-27 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_customuser_accountnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='accountNumber',
            field=models.CharField(default='3282dd', max_length=6, unique=True, verbose_name='Account Number'),
        ),
    ]