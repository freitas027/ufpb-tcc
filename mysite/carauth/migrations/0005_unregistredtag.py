# Generated by Django 3.0.2 on 2020-01-26 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carauth', '0004_tag_uid'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnregistredTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.CharField(max_length=50)),
                ('time', models.DateTimeField()),
            ],
        ),
    ]
