"""
Menu Item Schemas - Pydantic Models for API
With allergen tracking and multi-tag category system
"""

from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Allergen & Tag Enums
# ============================================================================

# Main categories (single-select)
MainCategory = Literal["protein", "premium_protein", "appetizer", "addon", "sauce"]

# Common tag values (for reference, not enforced)
PROTEIN_TYPE_TAGS = ["poultry", "seafood", "beef", "vegetarian"]
SEAFOOD_SUBTYPES = ["fish", "shellfish", "crustaceans", "mollusks"]
PREPARATION_TAGS = ["grilled", "steamed", "pan_fried", "raw"]
DIETARY_TAGS = ["gluten_free", "dairy_free"]

# FDA Major 9 Allergens + Emerging
ALLERGEN_TAGS = [
    # FDA Major 9
    "contains_shellfish",
    "contains_crustaceans",
    "contains_mollusks",
    "contains_fish",
    "contains_gluten",
    "contains_soy",
    "contains_eggs",
    "contains_tree_nuts",
    "contains_peanuts",
    "contains_dairy",
    # Emerging/Rare
    "contains_sesame",
    "contains_sulfites",
    "contains_msg",
    "contains_nightshades",
    "contains_corn",
    "contains_mustard",
    "contains_celery",
    "contains_lupin",
]


# ============================================================================
# Base Schemas
# ============================================================================


class MenuItemBase(BaseModel):
    """Base menu item fields (shared between create/update/response)"""

    name: str = Field(..., min_length=1, max_length=200, description="Menu item name")
    description: str = Field(..., min_length=1, max_length=1000, description="Item description")
    main_category: MainCategory = Field(..., description="Primary category")
    tags: list[str] = Field(
        default_factory=list,
        description="Multi-select tags: protein type, preparation, dietary, allergens",
    )
    base_price_per_person: Decimal = Field(
        ..., ge=0, decimal_places=2, description="Price per person (USD)"
    )
    is_included: bool = Field(default=False, description="Included in base menu price?")
    is_available: bool = Field(default=True, description="Currently available?")
    seasonal: bool = Field(default=False, description="Seasonal item?")
    display_order: int = Field(default=0, ge=0, description="Sort order in category")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and unique"""
        if not isinstance(v, list):
            raise ValueError("tags must be a list")
        # Convert to lowercase and remove duplicates
        return list(set(tag.lower().strip() for tag in v if tag))


class MenuItemCreate(MenuItemBase):
    """Schema for creating a new menu item"""

    pass


class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item (all fields optional)"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    main_category: Optional[MainCategory] = None
    tags: Optional[list[str]] = None
    base_price_per_person: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_included: Optional[bool] = None
    is_available: Optional[bool] = None
    seasonal: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Ensure tags are lowercase and unique"""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("tags must be a list")
        return list(set(tag.lower().strip() for tag in v if tag))


class MenuItemResponse(MenuItemBase):
    """Schema for menu item responses (includes DB fields)"""

    id: UUID
    ingredients: list[str] = Field(default_factory=list, description="Ingredient list (JSONB)")

    class Config:
        from_attributes = True


# ============================================================================
# Allergen Query Schemas
# ============================================================================


class AllergenQueryRequest(BaseModel):
    """Request to find items with/without specific allergen"""

    allergen_tag: str = Field(
        ...,
        description="Allergen tag to search for (e.g., 'contains_shellfish')",
        pattern="^contains_",
    )
    exclude: bool = Field(
        default=False,
        description="If True, return items WITHOUT this allergen. If False, return items WITH it.",
    )


class AllergenQueryResponse(BaseModel):
    """Response with allergen-filtered menu items"""

    allergen_tag: str
    exclude: bool
    items: list[MenuItemResponse]
    total_count: int


class DietaryFilterRequest(BaseModel):
    """Request to filter menu by dietary requirements"""

    required_tags: list[str] = Field(
        ..., min_length=1, description="Tags that items MUST have (AND logic)"
    )
    excluded_tags: list[str] = Field(
        default_factory=list, description="Tags that items must NOT have"
    )
    main_category: Optional[MainCategory] = Field(
        None, description="Optional: filter by main category"
    )


class DietaryFilterResponse(BaseModel):
    """Response with dietary-filtered menu items"""

    required_tags: list[str]
    excluded_tags: list[str]
    main_category: Optional[MainCategory]
    items: list[MenuItemResponse]
    total_count: int


# ============================================================================
# Menu Item List & Summary Schemas
# ============================================================================


class MenuItemListResponse(BaseModel):
    """Paginated list of menu items"""

    items: list[MenuItemResponse]
    total_count: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    total_pages: int


class MenuSummaryByCategory(BaseModel):
    """Summary statistics by category"""

    main_category: MainCategory
    total_items: int
    available_items: int
    gluten_free_count: int
    dairy_free_count: int
    shellfish_count: int
    average_price: Decimal


class MenuSummaryResponse(BaseModel):
    """Overall menu statistics"""

    total_items: int
    categories: list[MenuSummaryByCategory]
    unique_tags: list[str]
    allergen_summary: dict[str, int]  # allergen_tag -> count


# ============================================================================
# AI Agent Context Schemas
# ============================================================================


class MenuItemAIContext(BaseModel):
    """Simplified menu item for AI agent context"""

    name: str
    main_category: MainCategory
    tags: list[str]
    base_price_per_person: Decimal
    is_available: bool

    # Computed fields for AI clarity
    @property
    def is_gluten_free(self) -> bool:
        return "gluten_free" in self.tags

    @property
    def is_dairy_free(self) -> bool:
        return "dairy_free" in self.tags

    @property
    def is_vegetarian(self) -> bool:
        return "vegetarian" in self.tags

    @property
    def allergens(self) -> list[str]:
        """Extract allergen tags"""
        return [tag for tag in self.tags if tag.startswith("contains_")]

    @property
    def protein_type(self) -> Optional[str]:
        """Get protein type if applicable"""
        for tag in self.tags:
            if tag in PROTEIN_TYPE_TAGS:
                return tag
        return None

    @property
    def preparation_method(self) -> Optional[str]:
        """Get preparation method if applicable"""
        for tag in self.tags:
            if tag in PREPARATION_TAGS:
                return tag
        return None


class MenuContextForAI(BaseModel):
    """Complete menu context for AI agents"""

    all_items: list[MenuItemAIContext]
    gluten_free_items: list[MenuItemAIContext]
    dairy_free_items: list[MenuItemAIContext]
    vegetarian_items: list[MenuItemAIContext]
    shellfish_items: list[MenuItemAIContext]
    fish_items: list[MenuItemAIContext]

    # Business rules (for AI system prompt)
    business_rules: dict[str, str] = {
        "dairy_policy": "ALL items are dairy-free (we use dairy-free butter)",
        "gluten_free_exceptions": "Gyoza, Egg Noodles, Teriyaki Sauce contain gluten",
        "gluten_free_alternative": "Gluten-free soy sauce available as substitute",
        "no_pork": "We do not serve pork products",
        "shellfish_types": "Crustaceans (shrimp, lobster) and Mollusks (scallops)",
    }


# ============================================================================
# Bulk Operations
# ============================================================================


class BulkMenuItemCreate(BaseModel):
    """Create multiple menu items at once"""

    items: list[MenuItemCreate] = Field(..., min_length=1, max_length=100)


class BulkMenuItemCreateResponse(BaseModel):
    """Response from bulk create"""

    created_items: list[MenuItemResponse]
    total_created: int
    errors: list[dict[str, str]] = Field(
        default_factory=list, description="List of errors (if any)"
    )


class BulkTagUpdate(BaseModel):
    """Add or remove tags from multiple items"""

    item_ids: list[UUID] = Field(..., min_length=1)
    tags_to_add: list[str] = Field(default_factory=list)
    tags_to_remove: list[str] = Field(default_factory=list)


class BulkTagUpdateResponse(BaseModel):
    """Response from bulk tag update"""

    updated_items: list[MenuItemResponse]
    total_updated: int
