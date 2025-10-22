"""Activity partition property page."""


from gaphor import UML
from gaphor.core import transactional
from gaphor.diagram.propertypages import (
    PropertyPageBase,
    PropertyPages,
    combo_box_text_auto_complete,
    new_resource_builder,
)
from gaphor.UML.actions.partition import PartitionItem

new_builder = new_resource_builder("gaphor.UML.actions")


@PropertyPages.register(PartitionItem)
class PartitionPropertyPage(PropertyPageBase):
    """Partition property page."""

    order = 15

    def __init__(self, item: PartitionItem):
        super().__init__()
        self.item = item
        self.partitions = None

    def construct(self):
        """Creates the Partition Property Page."""
        builder = new_builder(
            "partition-editor",
            "num-partitions-adjustment",
            signals={"partitions-changed": (self._on_num_partitions_changed,)},
        )

        num_partitions = builder.get_object("num-partitions")
        num_partitions.set_value(len(self.item.partition))

        self.partitions = builder.get_object("partitions")
        if self.partitions:
            for partition in self.item.partition:
                self.partitions.append(self.construct_partition(partition))

        return builder.get_object("partition-editor")

    def construct_partition(self, partition):
        builder = new_builder(
            "partition",
            signals={
                "partition-name-changed": (self._on_partition_name_changed, partition),
                "partition-type-changed": (self._on_partition_type_changed, partition),
            },
        )

        builder.get_object("partition-name").set_text(partition.name or "")

        combo = builder.get_object("partition-type")
        combo_box_text_auto_complete(
            combo,
            (
                (c.id, c.name)
                for c in self.item.model.select(UML.Classifier)
                if c.name and not isinstance(c, UML.Behavior)
            ),
        )
        if partition.represents:
            combo.set_active_id(partition.represents.id)

        return builder.get_object("partition")

    @transactional
    def _on_num_partitions_changed(self, spin_button):
        """Event handler for partition number spin button."""
        num_partitions = spin_button.get_value_as_int()
        self.update_partitions(num_partitions)

    @transactional
    def _on_partition_name_changed(self, entry, partition):
        """Event handler for editing partition names."""
        partition.name = entry.get_text()

    @transactional
    def _on_partition_type_changed(self, combo, partition):
        """Event handler for editing partition names."""
        if id := combo.get_active_id():
            element = self.item.model.lookup(id)
            partition.represents = element
        else:
            del partition.represents

    def update_partitions(self, num_partitions) -> None:
        """Add and remove partitions.

        Clear the list store, then add or remove UML.ActivityPartitions
        to account for updates in the number of partitions, and finally
        rebuild the list store.
        """
        if not self.item.subject or not self.partitions:
            return

        while num_partitions > len(self.item.partition):
            partition = self.item.subject.model.create(UML.ActivityPartition)
            partition.name = self.item.diagram.gettext("New Swimlane")
            partition.activity = self.item.subject.activity
            self.item.partition.append(partition)

            self.partitions.append(self.construct_partition(partition))
        while num_partitions < len(self.item.partition):
            partition = self.item.partition[-1]
            partition.unlink()

            last_child = self.partitions.get_last_child()
            self.partitions.remove(last_child)

        self.item.diagram.update_now(self.item.diagram.ownedPresentation)
