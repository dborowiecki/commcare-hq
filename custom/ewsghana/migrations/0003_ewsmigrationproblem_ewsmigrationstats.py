from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ewsghana', '0002_ewsextension'),
    ]

    operations = [
        migrations.CreateModel(
            name='EWSMigrationProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('domain', models.CharField(max_length=128, db_index=True)),
                ('object_id', models.CharField(max_length=128, null=True)),
                ('object_type', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=128)),
                ('external_id', models.CharField(max_length=128)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EWSMigrationStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('products_count', models.IntegerField(default=0)),
                ('locations_count', models.IntegerField(default=0)),
                ('supply_points_count', models.IntegerField(default=0)),
                ('sms_users_count', models.IntegerField(default=0)),
                ('web_users_count', models.IntegerField(default=0)),
                ('domain', models.CharField(max_length=128, db_index=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
