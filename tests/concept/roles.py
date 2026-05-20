"""
Berechtigungs-Engine fuer das Testkonzept (Anhang D).

Da die App-Domaene keine echte RBAC kennt, wird hier eine *Konzept*-
Engine deklariert, die die im Testkonzept festgehaltene Soll-Matrix
abbildet. Die Engine ist absichtlich pur (keine I/O), sodass sie
parametrisierte JUnit-aehnliche Tests vollstaendig deckt.

Die Engine wird zusaetzlich gegen das *reale* Lizenz-Gate
(services/license_gate.py) und den *realen* destructive-Marker in
core/interface.py kreuzgeprueft - siehe test_roles_permissions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class Action(str, Enum):
    GROUP_CREATE = "GROUP_CREATE"
    GROUP_DELETE = "GROUP_DELETE"
    OWNERSHIP_TRANSFER = "OWNERSHIP_TRANSFER"
    MEMBER_INVITE = "MEMBER_INVITE"
    MEMBER_REMOVE = "MEMBER_REMOVE"
    MEMBER_CHANGE_ROLE = "MEMBER_CHANGE_ROLE"
    TASK_CREATE = "TASK_CREATE"
    TASK_ASSIGN_SELF = "TASK_ASSIGN_SELF"
    TASK_ASSIGN_OTHER = "TASK_ASSIGN_OTHER"
    TASK_CLOSE_OWN = "TASK_CLOSE_OWN"
    TASK_CLOSE_OTHER = "TASK_CLOSE_OTHER"
    TASK_VIEW = "TASK_VIEW"
    COMMENT = "COMMENT"
    PUSH_SETTINGS_SELF = "PUSH_SETTINGS_SELF"
    DATA_EXPORT = "DATA_EXPORT"


# Soll-Matrix gemaess Anhang D.1
_MATRIX: dict[tuple[Role, Action], bool] = {
    # OWNER: alles
    **{(Role.OWNER, a): True for a in Action},
    # ADMIN
    (Role.ADMIN, Action.GROUP_CREATE):      False,
    (Role.ADMIN, Action.GROUP_DELETE):      False,
    (Role.ADMIN, Action.OWNERSHIP_TRANSFER): False,
    (Role.ADMIN, Action.MEMBER_INVITE):     True,
    (Role.ADMIN, Action.MEMBER_REMOVE):     True,
    (Role.ADMIN, Action.MEMBER_CHANGE_ROLE): True,   # ausser OWNER
    (Role.ADMIN, Action.TASK_CREATE):       True,
    (Role.ADMIN, Action.TASK_ASSIGN_SELF):  True,
    (Role.ADMIN, Action.TASK_ASSIGN_OTHER): True,
    (Role.ADMIN, Action.TASK_CLOSE_OWN):    True,
    (Role.ADMIN, Action.TASK_CLOSE_OTHER):  True,
    (Role.ADMIN, Action.TASK_VIEW):         True,
    (Role.ADMIN, Action.COMMENT):           True,
    (Role.ADMIN, Action.PUSH_SETTINGS_SELF): True,
    (Role.ADMIN, Action.DATA_EXPORT):       True,
    # MEMBER
    (Role.MEMBER, Action.GROUP_CREATE):      False,
    (Role.MEMBER, Action.GROUP_DELETE):      False,
    (Role.MEMBER, Action.OWNERSHIP_TRANSFER): False,
    (Role.MEMBER, Action.MEMBER_INVITE):     False,
    (Role.MEMBER, Action.MEMBER_REMOVE):     False,
    (Role.MEMBER, Action.MEMBER_CHANGE_ROLE): False,
    (Role.MEMBER, Action.TASK_CREATE):       True,
    (Role.MEMBER, Action.TASK_ASSIGN_SELF):  True,
    (Role.MEMBER, Action.TASK_ASSIGN_OTHER): False,
    (Role.MEMBER, Action.TASK_CLOSE_OWN):    True,
    (Role.MEMBER, Action.TASK_CLOSE_OTHER):  False,
    (Role.MEMBER, Action.TASK_VIEW):         True,
    (Role.MEMBER, Action.COMMENT):           True,
    (Role.MEMBER, Action.PUSH_SETTINGS_SELF): True,
    (Role.MEMBER, Action.DATA_EXPORT):       False,
    # GUEST
    (Role.GUEST, Action.GROUP_CREATE):      False,
    (Role.GUEST, Action.GROUP_DELETE):      False,
    (Role.GUEST, Action.OWNERSHIP_TRANSFER): False,
    (Role.GUEST, Action.MEMBER_INVITE):     False,
    (Role.GUEST, Action.MEMBER_REMOVE):     False,
    (Role.GUEST, Action.MEMBER_CHANGE_ROLE): False,
    (Role.GUEST, Action.TASK_CREATE):       False,
    (Role.GUEST, Action.TASK_ASSIGN_SELF):  False,
    (Role.GUEST, Action.TASK_ASSIGN_OTHER): False,
    (Role.GUEST, Action.TASK_CLOSE_OWN):    False,
    (Role.GUEST, Action.TASK_CLOSE_OTHER):  False,
    (Role.GUEST, Action.TASK_VIEW):         True,
    (Role.GUEST, Action.COMMENT):           True,
    (Role.GUEST, Action.PUSH_SETTINGS_SELF): True,
    (Role.GUEST, Action.DATA_EXPORT):       False,
}


@dataclass(frozen=True)
class Permission:
    role: Role
    action: Action


def is_allowed(p: Permission) -> bool:
    """Soll-Antwort fuer eine Rolle/Aktion-Kombination."""
    return _MATRIX[(p.role, p.action)]


def all_permissions() -> list[Permission]:
    return [Permission(r, a) for r in Role for a in Action]
