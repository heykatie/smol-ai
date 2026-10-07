import pytest
from smolstuff.shop_memberships import MembershipStore
from smolstuff.shop_migrations import migrate_sqlite
from smolstuff.shop_access import authorize

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    migrate_sqlite(tmp_path / 'accounts.sqlite3')
    result = MembershipStore(str(tmp_path / 'accounts.sqlite3'))
    yield result
    result.close()

def test_identity_mapping_and_memberships_survive_restart(store):
    uid = store.provision_user('provider', 'verified-subject')
    assert store.provision_user('provider', 'verified-subject') == uid
    other = store.provision_user('other-provider', 'verified-subject')
    assert other != uid
    shop = store.provision_shop('keyboard', practice=True)
    store.provision_membership(uid, shop.shop_id, 'owner')
    reopened = MembershipStore(store.path)
    try:
        assert reopened.user_for_identity('provider', 'verified-subject') == uid
        membership = reopened.membership(uid, shop.shop_id)
        assert membership.role == 'owner'
        assert reopened.shop(shop.shop_id) == shop
        assert reopened.membership(other, shop.shop_id) is None
    finally:
        reopened.close()

def test_no_auto_account_or_membership_for_unknown_identity(store):
    assert store.user_for_identity('provider', 'unknown') is None
    assert store.membership('unknown', 'unknown') is None

def test_owner_delegation_is_scoped_and_reversible(store):
    owner = store.provision_user('p', 'owner')
    employee = store.provision_user('p', 'employee')
    stranger = store.provision_user('p', 'stranger')
    shop = store.provision_shop('bakery', practice=True)
    other_shop = store.provision_shop('keyboard', practice=False)
    store.provision_membership(owner, shop.shop_id, 'owner')
    store.provision_membership(employee, shop.shop_id, 'employee')
    store.provision_membership(stranger, other_shop.shop_id, 'owner')
    with pytest.raises(PermissionError):
        store.set_delegations(employee, shop.shop_id, employee, {'approve_correction'})
    with pytest.raises(PermissionError):
        store.set_delegations(stranger, shop.shop_id, employee, {'approve_correction'})
    store.set_delegations(owner, shop.shop_id, employee, {'approve_correction'})
    m = store.membership(employee, shop.shop_id)
    assert authorize(m, shop.shop_id, 'approve_correction', requester_id=owner)
    assert not authorize(m, shop.shop_id, 'approve_spending')
    assert not authorize(m, shop.shop_id, 'approve_correction', requester_id=employee)
    store.set_delegations(owner, shop.shop_id, employee, set())
    assert not authorize(store.membership(employee, shop.shop_id), shop.shop_id, 'approve_correction', requester_id=owner)
    assert len(store.permission_events(shop.shop_id)) == 2
    assert store.permission_events(other_shop.shop_id) == []

def test_inactive_memberships_cannot_authorize_or_delegate(store):
    owner = store.provision_user('p', 'owner')
    employee = store.provision_user('p', 'employee')
    shop = store.provision_shop('bakery', practice=True)
    store.provision_membership(owner, shop.shop_id, 'owner', active=False)
    store.provision_membership(employee, shop.shop_id, 'employee', active=False)
    assert not authorize(store.membership(employee, shop.shop_id), shop.shop_id, 'view_inventory')
    with pytest.raises(PermissionError): store.set_delegations(owner, shop.shop_id, employee, {'approve_correction'})

def test_invalid_grants_leave_no_changes_or_audit_event(store):
    owner = store.provision_user('p', 'owner')
    employee = store.provision_user('p', 'employee')
    shop = store.provision_shop('bakery', practice=True)
    store.provision_membership(owner, shop.shop_id, 'owner')
    store.provision_membership(employee, shop.shop_id, 'employee')
    with pytest.raises(ValueError): store.set_delegations(owner, shop.shop_id, employee, {'manage_members'})
    assert store.membership(employee, shop.shop_id).delegated == frozenset()
    assert store.permission_events(shop.shop_id) == []

def test_dangling_membership_rejected_and_identity_never_reassigned(store):
    with pytest.raises(ValueError): store.provision_membership('missing', 'missing', 'owner')
    uid = store.provision_user('p', 'owner')
    shop = store.provision_shop('keyboard', practice=True)
    store.provision_membership(uid, shop.shop_id, 'owner')
    with pytest.raises(ValueError): store.provision_membership(uid, shop.shop_id, 'employee')
    assert store.membership(uid, shop.shop_id).role == 'owner'
