import pytest
from smolstuff.shop_access import Membership, Shop, authorize, enabled_features, practice_accounts

def test_practice_accounts_share_only_their_own_shop():
    accounts = practice_accounts()
    assert len(accounts) == 4
    assert len({m.user_id for m in accounts}) == 4
    for shop_id in ('practice-keyboard', 'practice-bakery'):
        assert {m.role for m in accounts if m.shop_id == shop_id} == {'owner', 'employee'}
    employee = next(m for m in accounts if m.role == 'employee')
    assert authorize(employee, employee.shop_id, 'view_inventory')
    assert not authorize(employee, 'another-shop', 'view_inventory')

def test_employees_prepare_but_cannot_commit_or_approve():
    employee = Membership('employee', 'shop', 'employee')
    for action in ('view_inventory', 'submit_correction', 'prepare_recommendation'):
        assert authorize(employee, 'shop', action)
    for action in ('approve_correction', 'approve_spending', 'edit_inventory', 'manage_members'):
        assert not authorize(employee, 'shop', action)

def test_schedule_and_availability_are_personal():
    employee = Membership('employee', 'shop', 'employee')
    for action in ('view_schedule', 'submit_availability'):
        assert authorize(employee, 'shop', action, subject_user_id='employee')
        assert not authorize(employee, 'shop', action, subject_user_id='other')
        assert not authorize(employee, 'shop', action)

def test_delegated_approval_is_specific_and_blocks_self_approval():
    approver = Membership('reviewer', 'shop', 'employee', frozenset({'approve_correction'}))
    assert authorize(approver, 'shop', 'approve_correction', requester_id='other')
    assert not authorize(approver, 'shop', 'approve_correction', requester_id='reviewer')
    assert not authorize(approver, 'shop', 'approve_correction')
    assert not authorize(approver, 'shop', 'approve_spending', requester_id='other')
    owner = Membership('owner', 'shop', 'owner')
    assert not authorize(owner, 'shop', 'approve_correction', requester_id='owner')
    assert authorize(owner, 'shop', 'approve_correction', requester_id='other')

def test_missing_inactive_or_unknown_authority_fails_closed():
    assert not authorize(None, 'shop', 'view_inventory')
    assert not authorize(Membership('u', 'shop', 'employee', active=False), 'shop', 'view_inventory')
    assert not authorize(Membership('u', 'shop', 'owner'), 'shop', 'unknown')
    with pytest.raises(ValueError): Membership('u', 'shop', 'manager')
    with pytest.raises(ValueError): Membership('u', 'shop', 'employee', frozenset({'manage_members'}))

def test_shop_type_features_are_independent_of_permissions():
    bakery = Shop('bakery', 'bakery', True)
    keyboard = Shop('keyboard', 'keyboard', True)
    assert 'expiration_tracking' in enabled_features(bakery)
    assert 'expiration_tracking' not in enabled_features(keyboard)
    assert 'compatibility_reference' in enabled_features(keyboard)
    assert 'inventory' in enabled_features(bakery) & enabled_features(keyboard)
    with pytest.raises(ValueError): Shop('shop', 'unsupported', True)


@pytest.mark.parametrize("action", ["view_schedule", "view_availability"])
def test_owner_team_reads_require_active_subject_membership_in_same_shop(action):
    owner = Membership("owner", "shop", "owner")
    subject = Membership("employee", "shop", "employee")
    assert authorize(owner, "shop", action, subject_user_id="employee", subject_membership=subject)
    assert not authorize(owner, "shop", action, subject_user_id="employee")
    for invalid in (
        Membership("employee", "other-shop", "employee"),
        Membership("employee", "shop", "employee", active=False),
        Membership("someone-else", "shop", "employee"),
    ):
        assert not authorize(owner, "shop", action, subject_user_id="employee", subject_membership=invalid)
    assert not authorize(owner, "other-shop", action, subject_user_id="employee", subject_membership=subject)
    assert not authorize(Membership("owner", "shop", "owner", active=False),
                         "shop", action, subject_user_id="employee", subject_membership=subject)


def test_employees_read_only_own_availability_and_cannot_use_team_context():
    employee = Membership("employee", "shop", "employee", frozenset({"approve_spending"}))
    assert authorize(employee, "shop", "view_availability", subject_user_id="employee")
    other = Membership("other", "shop", "employee")
    for action in ("view_schedule", "view_availability"):
        assert not authorize(employee, "shop", action, subject_user_id="other", subject_membership=other)
        assert not authorize(employee, "shop", action)


def test_owner_team_visibility_does_not_allow_editing_employee_availability():
    owner = Membership("owner", "shop", "owner")
    other = Membership("employee", "shop", "employee")
    assert authorize(owner, "shop", "submit_availability", subject_user_id="owner")
    assert not authorize(owner, "shop", "submit_availability",
                         subject_user_id="employee", subject_membership=other)
