from django.db import models
from django.utils import timezone

from sentry.backup.scopes import RelocationScope
from sentry.db.models import Model, region_silo_model
from sentry.db.models.base import sane_repr


@region_silo_model
class GroupHashMetadata(Model):
    __relocation_scope__ = RelocationScope.Excluded

    # GENERAL
    grouphash = models.OneToOneField(
        "sentry.GroupHash", related_name="_metadata", on_delete=models.CASCADE
    )
    date_added = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = "sentry"
        db_table = "sentry_grouphashmetadata"

    @property
    def group_id(self) -> int | None:
        return self.grouphash.group_id

    # def repr(self):
    #     self.group_id = self.grouphash.group_id
    #     return sane_repr("grouphash_id", "group_id")

    __repr__ = sane_repr("grouphash_id", "group_id")
    # __repr__ = sane_repr("grouphash_id")

    # def __repr__(self)-> str:
    #     self.group_id = self.grouphash.group_id
    #     default_repr = sane_repr("grouphash_id", "group_id")
