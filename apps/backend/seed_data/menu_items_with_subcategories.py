"""
Menu Items with Subcategories and Tags - Seed Data Examples

This shows how to populate menu items with the new hierarchical category system.

Category Hierarchy:
- category: Main classification (protein, premium_protein, appetizer, add_on, sauce, side, base)
- subcategory: Primary type (poultry, fish, shellfish, beef, pork, vegetarian, tofu)
- tags: Multi-dimensional attributes (allergens, dietary info, cooking style)
"""

MENU_ITEMS_EXAMPLES = [
    # ========================================
    # PROTEINS (Base - Included in meal)
    # ========================================
    {
        "id": "protein_chicken_001",
        "name": "Chicken",
        "description": "Tender grilled chicken breast with hibachi seasonings",
        "category": "POULTRY",  # Main category
        "subcategory": "poultry",  # Subcategory
        "tags": ["poultry", "grilled", "gluten_free", "dairy_free"],  # Multi-tags
        "base_price": 0.00,  # Included in base
        "is_premium": False,
        "is_available": True,
        "display_order": 1,
    },
    {
        "id": "protein_steak_001",
        "name": "Steak",
        "description": "USDA Choice sirloin steak grilled to perfection",
        "category": "BEEF",
        "subcategory": "beef",
        "tags": ["beef", "grilled", "gluten_free", "dairy_free"],
        "base_price": 0.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 2,
    },
    {
        "id": "protein_shrimp_001",
        "name": "Shrimp",
        "description": "Succulent jumbo shrimp grilled hibachi-style",
        "category": "SEAFOOD",
        "subcategory": "shellfish",  # ⚠️ CRITICAL: shellfish subcategory
        "tags": [
            "seafood",
            "shellfish",
            "grilled",
            "gluten_free",
            "dairy_free",
            "contains_shellfish",  # ⚠️ ALLERGEN WARNING TAG
        ],
        "base_price": 0.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 3,
    },
    {
        "id": "protein_salmon_001",
        "name": "Salmon",
        "description": "Fresh Atlantic salmon grilled with lemon butter",
        "category": "SEAFOOD",
        "subcategory": "fish",  # ✅ SAFE: fish (not shellfish)
        "tags": [
            "seafood",
            "fish",
            "grilled",
            "gluten_free",
            "dairy_free",
            # NO "contains_shellfish" tag - safe for shellfish allergies
        ],
        "base_price": 0.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 4,
    },
    {
        "id": "protein_tofu_001",
        "name": "Tofu",
        "description": "Grilled organic tofu with teriyaki glaze",
        "category": "VEGETARIAN",
        "subcategory": "tofu",
        "tags": [
            "vegetarian",
            "vegan",
            "tofu",
            "grilled",
            "dairy_free",
            # NOT gluten_free due to teriyaki sauce (contains soy sauce)
        ],
        "base_price": 0.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 5,
    },
    # ========================================
    # PREMIUM PROTEINS (Upgrades - Extra cost)
    # ========================================
    {
        "id": "premium_lobster_001",
        "name": "Lobster Tail",
        "description": "Fresh Maine lobster tail grilled with garlic butter",
        "category": "SEAFOOD",
        "subcategory": "shellfish",  # ⚠️ SHELLFISH
        "tags": [
            "seafood",
            "shellfish",
            "premium",
            "grilled",
            "gluten_free",
            "contains_shellfish",  # ⚠️ ALLERGEN
        ],
        "base_price": 15.00,  # Premium upgrade
        "is_premium": True,
        "is_available": True,
        "display_order": 1,
    },
    {
        "id": "premium_scallops_001",
        "name": "Sea Scallops",
        "description": "Pan-seared jumbo sea scallops",
        "category": "SEAFOOD",
        "subcategory": "shellfish",  # ⚠️ SHELLFISH
        "tags": [
            "seafood",
            "shellfish",
            "premium",
            "grilled",
            "gluten_free",
            "dairy_free",
            "contains_shellfish",  # ⚠️ ALLERGEN
        ],
        "base_price": 12.00,
        "is_premium": True,
        "is_available": True,
        "display_order": 2,
    },
    {
        "id": "premium_filet_001",
        "name": "Filet Mignon",
        "description": "8oz USDA Prime filet mignon",
        "category": "BEEF",
        "subcategory": "beef",
        "tags": ["beef", "premium", "grilled", "gluten_free", "dairy_free"],
        "base_price": 18.00,
        "is_premium": True,
        "is_available": True,
        "display_order": 3,
    },
    # ========================================
    # APPETIZERS
    # ========================================
    {
        "id": "appetizer_gyoza_001",
        "name": "Gyoza (Dumplings)",
        "description": "6 pan-fried pork dumplings",
        "category": "APPETIZER",
        "subcategory": "pork",
        "tags": [
            "appetizer",
            "pork",
            "fried",
            "contains_gluten",  # ⚠️ Dumpling wrapper contains wheat
        ],
        "base_price": 6.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 1,
    },
    {
        "id": "appetizer_edamame_001",
        "name": "Edamame",
        "description": "Steamed soybeans with sea salt",
        "category": "APPETIZER",
        "subcategory": "vegetarian",
        "tags": ["appetizer", "vegetarian", "vegan", "steamed", "gluten_free", "dairy_free"],
        "base_price": 5.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 2,
    },
    {
        "id": "appetizer_salad_001",
        "name": "House Salad",
        "description": "Mixed greens with ginger dressing",
        "category": "APPETIZER",
        "subcategory": "vegetarian",
        "tags": ["appetizer", "vegetarian", "vegan", "raw", "gluten_free", "dairy_free"],
        "base_price": 4.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 3,
    },
    # ========================================
    # ADD-ONS
    # ========================================
    {
        "id": "addon_rice_001",
        "name": "Extra Fried Rice",
        "description": "Additional serving of hibachi fried rice",
        "category": "SIDE",
        "subcategory": "vegetarian",
        "tags": [
            "add_on",
            "side",
            "vegetarian",
            "fried",
            "contains_eggs",  # ⚠️ Contains eggs
            "contains_soy",  # ⚠️ Soy sauce
        ],
        "base_price": 3.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 1,
    },
    {
        "id": "addon_veggies_001",
        "name": "Extra Vegetables",
        "description": "Additional grilled seasonal vegetables",
        "category": "VEGETABLE",
        "subcategory": "vegetarian",
        "tags": ["add_on", "vegetarian", "vegan", "grilled", "gluten_free", "dairy_free"],
        "base_price": 3.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 2,
    },
    {
        "id": "addon_noodles_001",
        "name": "Yakisoba Noodles",
        "description": "Stir-fried Japanese noodles",
        "category": "SIDE",
        "subcategory": "vegetarian",
        "tags": ["add_on", "side", "vegetarian", "fried", "contains_gluten"],  # ⚠️ Wheat noodles
        "base_price": 4.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 3,
    },
    # ========================================
    # SAUCES
    # ========================================
    {
        "id": "sauce_yum_yum_001",
        "name": "Yum Yum Sauce",
        "description": "Creamy Japanese white sauce",
        "category": "SAUCE",
        "subcategory": None,  # Sauces don't need subcategory
        "tags": ["sauce", "condiment", "gluten_free", "contains_eggs"],  # ⚠️ Mayo-based
        "base_price": 0.00,  # Included
        "is_premium": False,
        "is_available": True,
        "display_order": 1,
    },
    {
        "id": "sauce_ginger_001",
        "name": "Ginger Sauce",
        "description": "Tangy ginger dressing",
        "category": "SAUCE",
        "subcategory": None,
        "tags": ["sauce", "condiment", "vegan", "gluten_free", "dairy_free"],
        "base_price": 0.00,
        "is_premium": False,
        "is_available": True,
        "display_order": 2,
    },
]

# ========================================
# AI USAGE EXAMPLES
# ========================================

"""
Example AI Queries and Logic:

1. Customer asks: "I have a shellfish allergy, what can I eat?"

   AI Query:
   SELECT * FROM menu_items
   WHERE NOT (tags @> '["contains_shellfish"]')

   Result: Returns chicken, steak, salmon (fish is safe!), tofu, veggies, etc.
   AI Response: "Safe options: Chicken, Steak, Salmon (fish, not shellfish), Tofu, Vegetables"


2. Customer asks: "What seafood do you have?"

   AI Query:
   SELECT * FROM menu_items
   WHERE subcategory IN ('fish', 'shellfish')

   Result: Salmon, Shrimp, Lobster, Scallops
   AI Response: "We have Salmon (fish), and Shrimp, Lobster, Scallops (shellfish)"


3. Customer asks: "I'm allergic to shellfish but love seafood"

   AI Query:
   SELECT * FROM menu_items
   WHERE subcategory = 'fish'
   AND NOT (tags @> '["contains_shellfish"]')

   Result: Salmon
   AI Response: "Perfect! Our Salmon is safe for shellfish allergies - it's fish, not shellfish."


4. Customer asks: "What's vegan and gluten-free?"

   AI Query:
   SELECT * FROM menu_items
   WHERE tags @> '["vegan", "gluten_free"]'

   Result: Edamame, House Salad, Extra Vegetables
   AI Response: "Vegan & gluten-free options: Edamame, House Salad, Extra Vegetables"


5. Customer asks: "Can I get a 3rd protein?"

   AI Query:
   SELECT * FROM menu_items
   WHERE category IN ('POULTRY', 'BEEF', 'SEAFOOD', 'VEGETARIAN')
   AND is_available = true
   ORDER BY is_premium, base_price

   Result: All proteins (base + premium)
   AI Response: "3rd protein is an add-on. Choose from: [list proteins with prices]"
"""
