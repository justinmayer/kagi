# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-25 15:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_u2f', '0003_add_totp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='u2fkey',
            name='public_key',
            field=models.TextField(unique=True),
        ),
    ]
