# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocDomainMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document_id', models.CharField(max_length=100, db_index=True)),
                ('name', models.CharField(max_length=256, db_index=True)),
                ('last_modified', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
