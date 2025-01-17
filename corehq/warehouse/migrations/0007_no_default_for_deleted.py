# Generated by Django 1.10.7 on 2017-06-28 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0006_group_column_tweaks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domaindim',
            name='deleted',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='groupdim',
            name='deleted',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='locationdim',
            name='deleted',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='userdim',
            name='deleted',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='usergroupdim',
            name='deleted',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='userlocationdim',
            name='deleted',
            field=models.BooleanField(),
        ),
    ]
