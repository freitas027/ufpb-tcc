# Generated by Django 2.2.7 on 2020-03-14 02:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carauth', '0010_auto_20200313_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='login',
            name='arduino',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='carauth.Arduino'),
        ),
    ]
