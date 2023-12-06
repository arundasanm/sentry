# Generated by Django 3.2.20 on 2023-10-20 20:46

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import sentry.db.models.fields.array
import sentry.db.models.fields.bounded
import sentry.db.models.fields.foreignkey
import sentry.db.models.fields.hybrid_cloud_foreign_key
from sentry.new_migrations.migrations import CheckedMigration


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production. For
    # the most part, this should only be used for operations where it's safe to run the migration
    # after your code has deployed. So this should not be used for most operations that alter the
    # schema of a table.
    # Here are some things that make sense to mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that they can
    #   be monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   have ops run this and not block the deploy. Note that while adding an index is a schema
    #   change, it's completely safe to run the operation after the code has deployed.
    is_dangerous = False

    dependencies = [
        ("sentry", "0579_index_incident_trigger"),
        ("hybridcloud", "0006_add_apitokenreplica"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrgAuthTokenReplica",
            fields=[
                (
                    "id",
                    sentry.db.models.fields.bounded.BoundedBigAutoField(
                        primary_key=True, serialize=False
                    ),
                ),
                (
                    "orgauthtoken_id",
                    sentry.db.models.fields.hybrid_cloud_foreign_key.HybridCloudForeignKey(
                        "sentry.OrgAuthToken", db_index=True, on_delete="CASCADE"
                    ),
                ),
                ("token_hashed", models.TextField()),
                ("name", models.CharField(max_length=255)),
                ("scope_list", sentry.db.models.fields.array.ArrayField(null=True)),
                (
                    "created_by_id",
                    sentry.db.models.fields.hybrid_cloud_foreign_key.HybridCloudForeignKey(
                        "sentry.User", blank=True, db_index=True, null=True, on_delete="SET_NULL"
                    ),
                ),
                ("date_added", models.DateTimeField(default=django.utils.timezone.now)),
                ("date_deactivated", models.DateTimeField(blank=True, null=True)),
                (
                    "organization",
                    sentry.db.models.fields.foreignkey.FlexibleForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="sentry.organization"
                    ),
                ),
            ],
            options={
                "db_table": "hybridcloud_orgauthtokenreplica",
            },
        ),
    ]
