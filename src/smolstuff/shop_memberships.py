"""Trusted account provisioning and shop memberships, separate from demo sessions.

No public provisioning endpoints. Call identity lookup only after authenticating
the provider subject. Application-owned IDs survive changes in login UI.
"""
import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from smolstuff.database import postgres_connection
from smolstuff.shop_access import Membership, Shop, authorize
from smolstuff.shop_migrations import require_schema


class MembershipStore:
    def __init__(self, path):
        self.path = path
        self.connection = postgres_connection()
        self.postgres = self.connection is not None
        if not self.postgres:
            self.connection = sqlite3.connect(path, isolation_level=None, timeout=10)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys=ON")
        try:
            require_schema(self.connection, postgres=self.postgres)
        except Exception:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def user_for_identity(self, provider, subject):
        row = self.connection.execute('SELECT user_id FROM shop_identities WHERE provider = ? AND subject = ?',
                                      (provider, subject)).fetchone()
        return row['user_id'] if row else None

    def provision_user(self, provider, subject):
        if not provider or not subject:
            raise ValueError('Verified identity required.')
        uid = uuid4().hex
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            existing = self.user_for_identity(provider, subject)
            if existing:
                self.connection.commit()
                return existing
            self.connection.execute('INSERT INTO shop_users VALUES (?)', (uid,))
            self.connection.execute('INSERT INTO shop_identities VALUES (?, ?, ?) ON CONFLICT DO NOTHING',
                                    (provider, subject, uid))
            actual = self.user_for_identity(provider, subject)
            if actual != uid:
                self.connection.execute('DELETE FROM shop_users WHERE user_id = ?', (uid,))
            self.connection.commit()
            return actual
        except Exception:
            self.connection.rollback()
            raise

    def provision_shop(self, shop_type, *, practice):
        shop = Shop(uuid4().hex, shop_type, practice)
        self.connection.execute('INSERT INTO shops VALUES (?, ?, ?)',
                                (shop.shop_id, shop.shop_type, int(shop.practice)))
        return shop

    def shop(self, shop_id):
        row = self.connection.execute('SELECT * FROM shops WHERE shop_id = ?', (shop_id,)).fetchone()
        return Shop(row['shop_id'], row['shop_type'], bool(row['practice'])) if row else None

    def provision_membership(self, user_id, shop_id, role, *, active=True):
        membership = Membership(user_id, shop_id, role, active=active)
        if not self.shop(shop_id) or not self.connection.execute('SELECT user_id FROM shop_users WHERE user_id = ?', (user_id,)).fetchone():
            raise ValueError('User and shop must already exist.')
        if self.membership(user_id, shop_id) is not None:
            raise ValueError('Membership already exists; provisioning cannot replace it.')
        self.connection.execute('INSERT INTO shop_memberships VALUES (?, ?, ?, ?, ?)',
                                (user_id, shop_id, role, '[]', int(membership.active)))
        return membership

    def membership(self, user_id, shop_id, *, lock=False):
        sql = 'SELECT * FROM shop_memberships WHERE user_id = ? AND shop_id = ?'
        if lock and self.postgres:
            sql += ' FOR UPDATE'
        row = self.connection.execute(sql, (user_id, shop_id)).fetchone()
        return Membership(row['user_id'], row['shop_id'], row['role'],
                          frozenset(json.loads(row['delegated'])), bool(row['active'])) if row else None

    def set_delegations(self, actor_id, shop_id, target_id, grants):
        # Transactional authorization and update; no stale client role is accepted.
        grants = frozenset(grants)
        Membership(target_id, shop_id, 'employee', grants)
        self.connection.execute('BEGIN IMMEDIATE')
        try:
            actor = self.membership(actor_id, shop_id, lock=True)
            if not authorize(actor, shop_id, 'manage_members'):
                raise PermissionError('Owner membership required.')
            target = self.membership(target_id, shop_id, lock=True)
            if target is None or not target.active or target.role != 'employee':
                raise PermissionError('Active employee membership required.')
            encoded = json.dumps(sorted(grants))
            self.connection.execute('UPDATE shop_memberships SET delegated = ? WHERE user_id = ? AND shop_id = ?',
                                    (encoded, target_id, shop_id))
            self.connection.execute('INSERT INTO shop_permission_events VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (uuid4().hex, shop_id, actor_id, target_id,
                                     json.dumps(sorted(target.delegated)), encoded,
                                     datetime.now(timezone.utc).isoformat()))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def permission_events(self, shop_id):
        return [dict(row) for row in self.connection.execute(
            'SELECT * FROM shop_permission_events WHERE shop_id = ? ORDER BY created_at, event_id',
            (shop_id,)).fetchall()]
