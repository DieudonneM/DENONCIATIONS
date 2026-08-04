from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0012_commentaire_origine_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piecejointe',
            name='type_fichier',
            field=models.CharField(max_length=120),
        ),
    ]
