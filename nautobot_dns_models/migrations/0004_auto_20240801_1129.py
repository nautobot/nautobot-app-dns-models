# Generated by Django 3.2.25 on 2024-08-01 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ipam", "0039_alter_ipaddresstointerface_ip_address"),
        ("nautobot_dns_models", "0003_remove_dnszonemodel_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dnszonemodel",
            name="name",
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name="aaaarecordmodel",
            unique_together={("name", "address", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="arecordmodel",
            unique_together={("name", "address", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="cnamerecordmodel",
            unique_together={("name", "alias", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="mxrecordmodel",
            unique_together={("name", "mail_server", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="nsrecordmodel",
            unique_together={("name", "server", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="ptrrecordmodel",
            unique_together={("name", "ptrdname", "zone")},
        ),
        migrations.AlterUniqueTogether(
            name="txtrecordmodel",
            unique_together={("name", "text", "zone")},
        ),
    ]
