from django.db import migrations


def forward(apps, schema_editor):
    Application = apps.get_model("core", "Application")
    Application.objects.filter(name="Production Pipeline").update(
        name="Distribution Pipeline"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0111_alter_twofactorauthprovidermodel_user"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
