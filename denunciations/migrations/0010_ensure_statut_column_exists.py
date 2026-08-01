from django.db import migrations


def ensure_statut_column(apps, schema_editor):
    Incident = apps.get_model('denunciations', 'Incident')
    table_name = Incident._meta.db_table
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        columns = {
            col.name for col in connection.introspection.get_table_description(cursor, table_name)
        }

    if 'statut' not in columns:
        statut_field = Incident._meta.get_field('statut').clone()
        schema_editor.add_field(Incident, statut_field)

        with connection.cursor() as cursor:
            columns = {
                col.name
                for col in connection.introspection.get_table_description(cursor, table_name)
            }

    if 'status' in columns and 'statut' in columns:
        quoted_table = connection.ops.quote_name(table_name)
        quoted_status = connection.ops.quote_name('status')
        quoted_statut = connection.ops.quote_name('statut')

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {quoted_table}
                SET {quoted_statut} = {quoted_status}
                WHERE ({quoted_statut} IS NULL OR {quoted_statut} = 'nouvelle')
                  AND {quoted_status} IS NOT NULL
                """
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('denunciations', '0009_remove_legacy_province_and_employeur'),
    ]

    operations = [
        migrations.RunPython(ensure_statut_column, noop_reverse),
    ]
