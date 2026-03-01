"""
Repository layer for MenuItem persistence.
All SQL for the `menu_items` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.menu_item import MenuItem

logger = logging.getLogger(__name__)


class MenuRepository:
    """Data access layer for menu item records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing MenuRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, menu_item_id: int) -> Optional[MenuItem]:
        """Return a menu item by id or None if missing."""
        logger.trace("Fetching menu item id=%s", menu_item_id)
        row = self._conn.execute(
            "SELECT * FROM menu_items WHERE id = ?", (menu_item_id,)
        ).fetchone()
        return MenuItem.from_row(row) if row else None

    def get_by_item_id(self, item_id: int) -> Optional[MenuItem]:
        """Return the menu item for a given item id, if present."""
        logger.trace("Fetching menu item item_id=%s", item_id)
        row = self._conn.execute(
            "SELECT * FROM menu_items WHERE item_id = ?", (item_id,)
        ).fetchone()
        return MenuItem.from_row(row) if row else None

    def list_all(self) -> list[MenuItem]:
        """Return all menu items ordered by item id."""
        logger.trace("Listing menu items")
        rows = self._conn.execute(
            "SELECT * FROM menu_items ORDER BY item_id"
        ).fetchall()
        return [MenuItem.from_row(r) for r in rows]

    def list_public(self) -> list[dict]:
        """Return menu items with the public field subset."""
        logger.trace("Listing public menu items")
        rows = self._conn.execute(
            """
            SELECT
                mi.display_name AS display_name,
                mi.description  AS description,
                mi.allergens    AS allergens,
                i.image_url     AS image_url,
                i.unit_price    AS unit_price,
                i.discount_rate AS discount_rate
            FROM menu_items mi
            JOIN items i ON i.id = mi.item_id
            ORDER BY mi.display_name
            """
        ).fetchall()
        return [
            {
                "display_name": r["display_name"],
                "image_url": r["image_url"],
                "description": r["description"],
                "unit_price": r["unit_price"],
                "allergens": r["allergens"],
                "discount_rate": r["discount_rate"],
            }
            for r in rows
        ]

    def list_grouped_by_category_public(self) -> list[dict]:
        """
        Return menu items grouped by category (public field subset).

        Each dict in the returned list has:
            category_id   – int
            category_name – str
            sort_order    – int
            items         – list[dict] with keys:
                              display_name, image_url, description, unit_price,
                              allergens, discount_rate
        """
        logger.trace("Listing menu items grouped by category (public)")
        rows = self._conn.execute(
            """
            SELECT
                c.id            AS category_id,
                c.name          AS category_name,
                c.sort_order    AS sort_order,
                mi.display_name AS display_name,
                mi.description  AS description,
                mi.allergens    AS allergens,
                i.image_url     AS image_url,
                i.unit_price    AS unit_price,
                i.discount_rate AS discount_rate
            FROM menu_items mi
            JOIN items i      ON i.id = mi.item_id
            JOIN categories c ON c.id = i.category_id
            ORDER BY c.sort_order, c.name, mi.display_name
            """
        ).fetchall()

        groups: dict[int, dict] = {}
        for r in rows:
            cid = r["category_id"]
            if cid not in groups:
                groups[cid] = {
                    "category_id": cid,
                    "category_name": r["category_name"],
                    "sort_order": r["sort_order"],
                    "items": [],
                }
            groups[cid]["items"].append(
                {
                    "display_name": r["display_name"],
                    "image_url": r["image_url"],
                    "description": r["description"],
                    "unit_price": r["unit_price"],
                    "allergens": r["allergens"],
                    "discount_rate": r["discount_rate"],
                }
            )

        return list(groups.values())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(
        self,
        item_id: int,
        display_name: str,
        description: Optional[str],
        allergens: Optional[str],
        created_by: int,
    ) -> MenuItem:
        """Insert a menu item row and return it."""
        logger.info("Creating menu item item_id=%s", item_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO menu_items (
                item_id, display_name, description, allergens,
                created_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, display_name, description, allergens, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def delete(self, item_id: int) -> bool:
        """Delete a menu item by item id and return True if removed."""
        logger.info("Deleting menu item item_id=%s", item_id)
        cursor = self._conn.execute(
            "DELETE FROM menu_items WHERE item_id = ?", (item_id,)
        )
        logger.info("Menu item delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0
