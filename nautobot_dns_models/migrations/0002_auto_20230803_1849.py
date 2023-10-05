# Generated by Django 3.2.18 on 2023-08-03 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("nautobot_dns_models", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aaaarecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aaaarecordmodel",
                related_query_name="aaaarecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
        migrations.AlterField(
            model_name="arecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="arecordmodel",
                related_query_name="arecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
        migrations.AlterField(
            model_name="cnamerecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cnamerecordmodel",
                related_query_name="cnamerecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
        migrations.AlterField(
            model_name="mxrecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="mxrecordmodel",
                related_query_name="mxrecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
        migrations.AlterField(
            model_name="nsrecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="nsrecordmodel",
                related_query_name="nsrecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
        migrations.AlterField(
            model_name="txtrecordmodel",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="txtrecordmodel",
                related_query_name="txtrecordmodel",
                to="nautobot_dns_models.dnszonemodel",
            ),
        ),
    ]
