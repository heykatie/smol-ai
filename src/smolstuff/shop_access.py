"""Provider-independent shop permissions; not authentication or a persistence layer.

Memberships must come from trusted server records, never request parameters.
Feature flags express eligibility, not evidence that a feature is implemented.
"""
from dataclasses import dataclass
from typing import FrozenSet, Optional

COMMON = frozenset({'inventory', 'correction_requests', 'schedules', 'availability', 'recommendations'})
EMPLOYEE = frozenset({'view_inventory', 'submit_correction', 'prepare_recommendation',
                      'view_schedule', 'submit_availability'})
DELEGATABLE = frozenset({'approve_correction', 'approve_spending'})
OWNER = EMPLOYEE | DELEGATABLE | frozenset({'manage_members'})


@dataclass(frozen=True)
class Shop:
    shop_id: str
    shop_type: str
    practice: bool

    def __post_init__(self):
        if not self.shop_id or self.shop_type not in {'keyboard', 'bakery'}:
            raise ValueError('Invalid shop configuration.')


@dataclass(frozen=True)
class Membership:
    user_id: str
    shop_id: str
    role: str
    delegated: FrozenSet[str] = frozenset()
    active: bool = True

    def __post_init__(self):
        if not self.user_id or not self.shop_id or self.role not in {'owner', 'employee'}:
            raise ValueError('Invalid membership.')
        grants = frozenset(self.delegated)
        if not grants <= DELEGATABLE:
            raise ValueError('Invalid delegated permissions.')
        object.__setattr__(self, 'delegated', grants)


def authorize(membership: Optional[Membership], shop_id: str, action: str,
              *, requester_id: Optional[str] = None, subject_user_id: Optional[str] = None) -> bool:
    if membership is None or not membership.active or membership.shop_id != shop_id:
        return False
    permissions = OWNER if membership.role == 'owner' else EMPLOYEE | membership.delegated
    if action not in permissions:
        return False
    if action == 'approve_correction' and (not requester_id or requester_id == membership.user_id):
        return False
    if action in {'view_schedule', 'submit_availability'}:
        return subject_user_id == membership.user_id
    return True


def enabled_features(shop: Shop) -> FrozenSet[str]:
    return COMMON | frozenset({'expiration_tracking'} if shop.shop_type == 'bakery'
                              else {'compatibility_reference'})


def practice_accounts():
    """Synthetic identities for seeding later; creates no provider accounts or login bypass."""
    return tuple(Membership(shop + '-' + role, shop, role)
                 for shop in ('practice-keyboard', 'practice-bakery')
                 for role in ('owner', 'employee'))
