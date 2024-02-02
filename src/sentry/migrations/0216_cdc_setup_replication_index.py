# Generated by Django 1.11.29 on 2021-06-30 18:51

from django.db import migrations


def set_replication_identity(schema_editor, model, column_names):
    cursor = schema_editor.connection.cursor()
    # This gets the current list of constraint names on the model based on the provided parameters.
    # We are specifically looking for matching column names and unique indexes since replication
    # identities only work on unique constraints
    unique_constraint_names = schema_editor._constraint_names(model, column_names, unique=True)

    if not unique_constraint_names:
        # Create a unique index since there is no unique index on the columns we want.
        index = schema_editor._create_index_name(model._meta.db_table, column_names, "_uniq")

        cursor.execute(
            f'CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS {schema_editor.quote_name(index)} ON {schema_editor.quote_name(model._meta.db_table)} ({", ".join(schema_editor.quote_name(col) for col in column_names)});'
        )
    else:
        # There should ideally be only one. But even if there are more, lets use the first one
        index = unique_constraint_names[0]

    cursor.execute(
        f"ALTER TABLE {schema_editor.quote_name(model._meta.db_table)} REPLICA IDENTITY USING INDEX {schema_editor.quote_name(index)}"
    )
    cursor.close()


def reset_replication_identity(schema_editor, model):
    cursor = schema_editor.connection.cursor()
    cursor.execute(
        f"ALTER TABLE {schema_editor.quote_name(model._meta.db_table)} REPLICA IDENTITY DEFAULT"
    )
    cursor.close()


def set_groupassignee_replication_identity(apps, schema_editor):
    group_assignee_model = apps.get_model("sentry", "GroupAssignee")
    set_replication_identity(schema_editor, group_assignee_model, ["project_id", "group_id"])


def reset_groupassignee_replication_identity(apps, schema_editor):
    group_assignee_model = apps.get_model("sentry", "GroupAssignee")
    reset_replication_identity(schema_editor, group_assignee_model)


def set_groupedmessage_replication_identity(apps, schema_editor):
    group_model = apps.get_model("sentry", "Group")
    set_replication_identity(schema_editor, group_model, ["project_id", "id"])


def reset_groupedmessage_replication_identity(apps, schema_editor):
    group_model = apps.get_model("sentry", "Group")
    reset_replication_identity(schema_editor, group_model)


class Migration(migrations.Migration):
    # This flag is used to mark that a migration shouldn't be automatically run in
    # production. We set this to True for operations that we think are risky and want
    # someone from ops to run manually and monitor.
    # General advice is that if in doubt, mark your migration as `is_dangerous`.
    # Some things you should always mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that
    #   they can be monitored. Since data migrations will now hold a transaction open
    #   this is even more important.
    # - Adding columns to highly active tables, even ones that are NULL.
    is_dangerous = True

    # This flag is used to decide whether to run this migration in a transaction or not.
    # By default we prefer to run in a transaction, but for migrations where you want
    # to `CREATE INDEX CONCURRENTLY` this needs to be set to False. Typically you'll
    # want to create an index concurrently when adding one to an existing table.
    # You'll also usually want to set this to `False` if you're writing a data
    # migration, since we don't want the entire migration to run in one long-running
    # transaction.
    atomic = False

    dependencies = [
        ("sentry", "0215_fix_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=set_groupassignee_replication_identity,
                    reverse_code=reset_groupassignee_replication_identity,
                    atomic=False,
                    hints={"tables": ["sentry_groupasignee"]},
                )
            ],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="groupassignee",
                    unique_together={("project", "group")},
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=set_groupedmessage_replication_identity,
                    reverse_code=reset_groupedmessage_replication_identity,
                    atomic=False,
                    hints={"tables": ["sentry_groupedmessage"]},
                )
            ],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="group",
                    unique_together={("project", "id"), ("project", "short_id")},
                ),
            ],
        ),
    ]
