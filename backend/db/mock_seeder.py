"""
Mock data seeder – creates sample categories and items for testing.

⚠️  FOR DEVELOPMENT ONLY.
    This seeder creates test data automatically on startup.
    Remove the call from main.py before deploying to production.
"""
import logging
import random

from backend.db.database import get_connection
from backend.repositories.category_repository import CategoryRepository
from backend.repositories.item_repository import ItemRepository
from backend.repositories.stock_repository import StockRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.menu_repository import MenuRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_CATEGORIES = [
    {"name": "Fresh Produce", "description": "Fresh fruits and vegetables"},
    {"name": "Dairy & Eggs", "description": "Milk, cheese, yogurt, and eggs"},
    {"name": "Bakery", "description": "Bread, pastries, and baked goods"},
    {"name": "Beverages", "description": "Coffee, tea, juices, and soft drinks"},
    {"name": "Meat & Seafood", "description": "Fresh and frozen meat and seafood"},
    {"name": "Pantry", "description": "Dry goods, canned items, and spices"},
    {"name": "Snacks", "description": "Chips, nuts, and confectionery"},
]

MOCK_ITEMS = {
    "Fresh Produce": [
        {"name": "Red Apples", "unit_type": "kg", "unit_price": 3.99, "tax_rate": 0},
        {"name": "Bananas", "unit_type": "kg", "unit_price": 2.49, "tax_rate": 0},
        {"name": "Carrots", "unit_type": "kg", "unit_price": 1.99, "tax_rate": 0},
        {"name": "Tomatoes", "unit_type": "kg", "unit_price": 4.99, "tax_rate": 0},
        {"name": "Lettuce", "unit_type": "piece", "unit_price": 2.29, "tax_rate": 0},
        {"name": "Potatoes", "unit_type": "kg", "unit_price": 1.79, "tax_rate": 0},
    ],
    "Dairy & Eggs": [
        {"name": "Whole Milk 1L", "unit_type": "piece", "unit_price": 2.99, "tax_rate": 0},
        {"name": "Cheddar Cheese 200g", "unit_type": "piece", "unit_price": 5.49, "tax_rate": 0},
        {"name": "Greek Yogurt", "unit_type": "piece", "unit_price": 3.29, "tax_rate": 0},
        {"name": "Free-Range Eggs (12)", "unit_type": "piece", "unit_price": 6.99, "tax_rate": 0},
        {"name": "Butter 250g", "unit_type": "piece", "unit_price": 4.49, "tax_rate": 0},
    ],
    "Bakery": [
        {"name": "Sourdough Bread", "unit_type": "piece", "unit_price": 5.99, "tax_rate": 0},
        {"name": "Croissant", "unit_type": "piece", "unit_price": 3.49, "tax_rate": 0},
        {"name": "Baguette", "unit_type": "piece", "unit_price": 3.29, "tax_rate": 0},
        {"name": "Chocolate Muffin", "unit_type": "piece", "unit_price": 3.99, "tax_rate": 0},
    ],
    "Beverages": [
        {"name": "Espresso Coffee", "unit_type": "cup", "unit_price": 3.50, "tax_rate": 10},
        {"name": "Cappuccino", "unit_type": "cup", "unit_price": 4.50, "tax_rate": 10},
        {"name": "Fresh Orange Juice", "unit_type": "piece", "unit_price": 4.99, "tax_rate": 0},
        {"name": "Green Tea", "unit_type": "cup", "unit_price": 3.00, "tax_rate": 10},
        {"name": "Still Water 500ml", "unit_type": "piece", "unit_price": 2.50, "tax_rate": 0},
    ],
    "Meat & Seafood": [
        {"name": "Chicken Breast", "unit_type": "kg", "unit_price": 12.99, "tax_rate": 0},
        {"name": "Ground Beef", "unit_type": "kg", "unit_price": 14.99, "tax_rate": 0},
        {"name": "Salmon Fillet", "unit_type": "kg", "unit_price": 28.99, "tax_rate": 0},
        {"name": "Prawns", "unit_type": "kg", "unit_price": 24.99, "tax_rate": 0},
    ],
    "Pantry": [
        {"name": "Olive Oil 500ml", "unit_type": "piece", "unit_price": 8.99, "tax_rate": 0},
        {"name": "Spaghetti 500g", "unit_type": "piece", "unit_price": 2.99, "tax_rate": 0},
        {"name": "Tomato Sauce", "unit_type": "piece", "unit_price": 3.49, "tax_rate": 0},
        {"name": "Basil Dried", "unit_type": "piece", "unit_price": 2.99, "tax_rate": 0},
        {"name": "Sea Salt", "unit_type": "piece", "unit_price": 2.49, "tax_rate": 0},
    ],
    "Snacks": [
        {"name": "Sea Salt Chips", "unit_type": "piece", "unit_price": 3.99, "tax_rate": 0},
        {"name": "Mixed Nuts", "unit_type": "piece", "unit_price": 6.99, "tax_rate": 0},
        {"name": "Dark Chocolate 70%", "unit_type": "piece", "unit_price": 4.99, "tax_rate": 0},
        {"name": "Granola Bar", "unit_type": "piece", "unit_price": 2.49, "tax_rate": 0},
    ],
}


def _generate_sku(category_name: str, item_name: str, index: int) -> str:
    """Generate a unique SKU for an item."""
    logger.trace("Generating SKU for item %s", item_name)
    cat_prefix = "".join(word[0].upper() for word in category_name.split() if word)
    item_prefix = "".join(word[0].upper() for word in item_name.split()[:2])
    return f"{cat_prefix}-{item_prefix}-{index:04d}"


def _generate_barcode(sku: str) -> str:
    """Generate a fake EAN-like barcode from the SKU."""
    logger.trace("Generating barcode for SKU=%s", sku)
    digits = "".join(str(ord(c) % 10) for c in sku)
    return (digits * 2)[:13]


def seed_mock_data() -> None:
    """
    Create mock categories, items, stock, carts, and menu items for testing.
    Uses the first available user as the creator (typically the admin).
    Safe to call multiple times – will skip already existing data.
    """
    logger.info("Mock seeder: starting")
    conn = get_connection()
    try:
        user_repo = UserRepository(conn)
        category_repo = CategoryRepository(conn)
        item_repo = ItemRepository(conn)
        stock_repo = StockRepository(conn)
        cart_repo = CartRepository(conn)
        menu_repo = MenuRepository(conn)

        # Get the first user (admin) to use as creator
        users = user_repo.list_all()
        if not users:
            logger.warning("Mock seeder: No users found. Skipping mock data creation.")
            return

        creator_id = users[0].id
        logger.info("Mock seeder: Using user id=%s as creator", creator_id)

        # Create categories
        category_map = {}  # name -> id
        for cat_data in MOCK_CATEGORIES:
            existing = category_repo.get_by_name(cat_data["name"])
            if existing:
                logger.info("Mock seeder: Category '%s' already exists", cat_data["name"])
                category_map[cat_data["name"]] = existing.id
            else:
                category = category_repo.create(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    created_by=creator_id,
                )
                category_map[cat_data["name"]] = category.id
                logger.info("Mock seeder: Created category '%s' (id=%s)", cat_data["name"], category.id)

        # Create items
        item_count = 0
        for category_name, items in MOCK_ITEMS.items():
            category_id = category_map.get(category_name)
            if not category_id:
                continue

            for idx, item_data in enumerate(items, start=1):
                sku = _generate_sku(category_name, item_data["name"], idx)
                
                # Check if item with this SKU already exists
                existing = item_repo.get_by_sku(sku)
                if existing:
                    logger.info("Mock seeder: Item with SKU '%s' already exists", sku)
                    continue

                barcode = _generate_barcode(sku)
                discount_rate = random.choice([0, 0, 0, 5, 10, 15])  # Random discount for variety

                item_repo.create(
                    category_id=category_id,
                    name=item_data["name"],
                    description=f"Fresh {item_data['name'].lower()} for your cafe or store",
                    sku=sku,
                    barcode=barcode,
                    image_url=None,
                    unit_price=float(item_data["unit_price"]),
                    unit_type=item_data["unit_type"],
                    tax_rate=float(item_data["tax_rate"]),
                    discount_rate=float(discount_rate),
                    created_by=creator_id,
                )
                item_count += 1

        logger.info("Mock seeder: Created %s new items", item_count)

        # ── Stock entries ──────────────────────────────────────────────────
        # Add every item to stock with a random initial quantity.
        all_items = item_repo.list_all()
        stock_count = 0
        for item in all_items:
            if stock_repo.get_by_item_id(item.id):
                logger.info("Mock seeder: Stock entry for item id=%s already exists", item.id)
                continue
            quantity = round(random.uniform(5.0, 200.0), 2)
            stock_repo.add(
                item_id=item.id,
                quantity=quantity,
                created_by=creator_id,
            )
            stock_count += 1

        logger.info("Mock seeder: Created %s new stock entries", stock_count)

        # ── Menu items ───────────────────────────────────────────────────────
        menu_count = 0
        for item in item_repo.list_all():
            if menu_repo.get_by_item_id(item.id):
                logger.info("Mock seeder: Menu item for item id=%s already exists", item.id)
                continue
            menu_repo.add(
                item_id=item.id,
                display_name=item.name,
                description=f"Menu listing for {item.name}",
                allergens=None,
                created_by=creator_id,
            )
            menu_count += 1

        logger.info("Mock seeder: Created %s menu items", menu_count)

        # ── Carts ────────────────────────────────────────────────────────────
        carts = []
        desk_numbers = ["A01", "A02", "B01"]
        for desk in desk_numbers:
            # Check if a cart with this desk_number already exists
            existing = cart_repo.get_by_desk_number(desk)
            if existing:
                logger.info("Mock seeder: Cart with desk_number '%s' already exists", desk)
                carts.append(existing)
                continue
            cart = cart_repo.create(created_by=creator_id)
            cart_repo.update_desk_number(cart.id, desk, creator_id)
            carts.append(cart_repo.get_by_id(cart.id))
        logger.info("Mock seeder: Created %s carts with desk numbers", len(carts))

        if carts:
            available_items = item_repo.list_all()
            for cart in carts:
                if not available_items:
                    continue
                for item in random.sample(available_items, k=min(3, len(available_items))):
                    stock_entry = stock_repo.get_by_item_id(item.id)
                    if not stock_entry or stock_entry.quantity <= 0:
                        continue
                    max_qty = max(1, int(min(5, stock_entry.quantity)))
                    cart_repo.create_cart_item(
                        cart_id=cart.id,
                        item_id=item.id,
                        quantity=random.randint(1, max_qty),
                        created_by=creator_id,
                    )
            logger.info("Mock seeder: Added items to carts")

        conn.commit()

    except Exception as e:
        logger.error("Mock seeder failed: %s", e)
        conn.rollback()
        raise
    finally:
        conn.close()