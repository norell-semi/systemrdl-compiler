"""
User-defined properties that are always pre-registered by the compiler, so
that every exporter interprets them consistently.

They are usable without being declared. For compatibility with other SystemRDL
tools, the RDL source may still declare them, as long as the declaration
matches the one in the file at :data:`RDL_PATH`.
"""
from typing import TYPE_CHECKING, Any, List, Type, cast
import os

from . import component as comp
from .udp import UDPDefinition

if TYPE_CHECKING:
    from .node import Node, RegNode

#: Path to the SystemRDL file that declares all built-in UDPs
RDL_PATH = os.path.join(os.path.dirname(__file__), "builtin_udps.rdl")


class Anonymous(UDPDefinition):
    """
    Marks a field as anonymous: it is the only field of its register and
    exporters shall not expose it as a separate level of hierarchy.
    For example, register ``EPID`` with an anonymous field is exposed as
    ``EPID`` rather than ``EPID.EPID`` / ``EPID__EPID``.
    """
    name = "anonymous"
    valid_components = {comp.Field}
    valid_type = bool
    default_assignment = True

    def validate(self, node: 'Node', value: Any) -> None:
        if not value:
            return

        reg = cast('RegNode', node.parent)
        n_fields = len(reg.fields(skip_not_present=False))
        if n_fields != 1:
            self.msg.error(
                "Field '%s' is marked as anonymous, but register '%s' contains %d fields. "
                "An anonymous field shall be the only field in its register."
                % (node.inst_name, reg.inst_name, n_fields),
                self.get_src_ref(node)
            )

    def get_unassigned_default(self, node: 'Node') -> Any:
        return False


ALL_BUILTIN_UDPS: List[Type[UDPDefinition]] = [
    Anonymous,
]


def get_rdl_declarations() -> str:
    """
    Returns the SystemRDL source text that declares all built-in UDPs
    """
    with open(RDL_PATH, "r", encoding="utf-8") as f:
        return f.read()
