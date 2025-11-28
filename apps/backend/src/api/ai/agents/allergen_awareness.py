"""
AI Agent Allergen Awareness System
Comprehensive allergen handling for MenuAgent with rare allergen explanations

UPDATED: November 27, 2025 - Verified ingredient information from kitchen operations
"""

from typing import Dict, List, Optional

from pydantic import BaseModel


# ============================================================================
# VERIFIED KITCHEN INGREDIENTS (Nov 2025)
# ============================================================================

VERIFIED_INGREDIENTS = {
    "cooking_oil": "canola",  # ✅ ALLERGEN-FREE, not soy
    "sesame_oil": False,  # ❌ NOT used
    "msg": False,  # ❌ NOT used
    "mustard": False,  # ❌ NOT used
    "celery": "salad_dressing_only",  # ⚠️ EU ALLERGEN PRESENT
    "bell_peppers": False,  # ❌ NOT used
    "sulfites": "sake_only",  # ⚠️ Natural in sake, no vinegar
    "corn_starch": "teriyaki_sauce",  # ⚠️ May be present
    "vinegar": False,  # ❌ NOT used
    "cross_contamination": True,  # ⚠️ SHARED cooking surfaces, utensils, oils
}

CROSS_CONTAMINATION_WARNING = """
⚠️ CRITICAL: We CANNOT guarantee 100% allergen-free environment.

We use:
- SHARED cooking surfaces (hibachi grill)
- SHARED utensils (spatulas, knives, tongs)
- SHARED oil (canola oil for all cooking)
- Airborne particles from shellfish, fish, soy sauce may be present

We CAN:
- Use clean utensils for severe allergies
- Cook allergen-free items separately when possible
- Alert chef via booking system

Customers with severe allergies must make informed decision about risk.
"""


# ============================================================================
# Allergen Knowledge Base
# ============================================================================


class AllergenInfo(BaseModel):
    """Complete information about an allergen"""

    tag: str
    name: str
    category: str  # 'major_fda' | 'emerging' | 'rare' | 'eu_specific'
    severity: str  # 'severe' | 'moderate' | 'rare'
    description: str
    reaction_types: List[str]
    prevalence: str
    cross_contamination_risk: str
    safe_alternatives_guidance: str


ALLERGEN_KNOWLEDGE_BASE: Dict[str, AllergenInfo] = {
    # ========================================================================
    # FDA MAJOR 9 ALLERGENS (90% of food allergies)
    # ========================================================================
    "contains_shellfish": AllergenInfo(
        tag="contains_shellfish",
        name="Shellfish",
        category="major_fda",
        severity="severe",
        description="Shellfish includes crustaceans (shrimp, lobster, crab) and mollusks (scallops, oysters, clams, mussels). This is one of the most common and severe food allergies.",
        reaction_types=[
            "Anaphylaxis",
            "Hives",
            "Swelling",
            "Breathing difficulty",
            "Digestive issues",
        ],
        prevalence="Affects ~2% of US population, often lifelong",
        cross_contamination_risk="HIGH - shared cooking surfaces, utensils, fryer oil",
        safe_alternatives_guidance="Fish (salmon) is NOT shellfish and may be safe. Chicken, steak, tofu are safe. Always verify customer can eat fish separately.",
    ),
    "contains_crustaceans": AllergenInfo(
        tag="contains_crustaceans",
        name="Crustaceans (Shrimp, Lobster, Crab)",
        category="major_fda",
        severity="severe",
        description="Crustaceans are a sub-type of shellfish with jointed shells. Includes shrimp, lobster, crab, crayfish. Different from mollusks (scallops).",
        reaction_types=["Anaphylaxis", "Hives", "Swelling", "Vomiting"],
        prevalence="Most common type of shellfish allergy",
        cross_contamination_risk="HIGH - shared cooking surfaces",
        safe_alternatives_guidance="Mollusks (scallops) may NOT be safe if customer says 'shellfish allergy'. Fish (salmon) is different. Verify which type of shellfish to avoid.",
    ),
    "contains_mollusks": AllergenInfo(
        tag="contains_mollusks",
        name="Mollusks (Scallops, Oysters, Clams)",
        category="major_fda",
        severity="severe",
        description="Mollusks are a sub-type of shellfish with single shells or no shells. Includes scallops, oysters, clams, mussels, squid.",
        reaction_types=["Anaphylaxis", "Hives", "Digestive issues"],
        prevalence="Less common than crustacean allergy but still serious",
        cross_contamination_risk="HIGH - shared cooking surfaces",
        safe_alternatives_guidance="Crustaceans (shrimp) may NOT be safe if customer says 'shellfish allergy'. Fish (salmon) is different. Verify which type of shellfish to avoid.",
    ),
    "contains_fish": AllergenInfo(
        tag="contains_fish",
        name="Fish (Finned Fish)",
        category="major_fda",
        severity="severe",
        description="Finned fish like salmon, tuna, cod, halibut. This is DIFFERENT from shellfish. Some people allergic to fish can eat shellfish and vice versa.",
        reaction_types=["Anaphylaxis", "Hives", "Digestive issues"],
        prevalence="Affects ~1% of US population",
        cross_contamination_risk="HIGH - shared cooking surfaces, oils",
        safe_alternatives_guidance="Shellfish (shrimp, scallops) are NOT fish and may be safe. Verify separately. Chicken, steak, tofu are safe.",
    ),
    "contains_gluten": AllergenInfo(
        tag="contains_gluten",
        name="Gluten (Wheat, Barley, Rye)",
        category="major_fda",
        severity="moderate",
        description="Protein in wheat, barley, rye. Causes celiac disease (autoimmune) or gluten sensitivity. Found in bread, pasta, noodles, soy sauce.",
        reaction_types=["Digestive issues", "Fatigue", "Joint pain", "Skin rash (celiac)"],
        prevalence="Celiac: ~1%, Gluten sensitivity: ~6%",
        cross_contamination_risk="MODERATE - flour dust, shared utensils",
        safe_alternatives_guidance="We have gluten-free soy sauce! Most items are naturally gluten-free except gyoza, egg noodles, teriyaki sauce.",
    ),
    "contains_soy": AllergenInfo(
        tag="contains_soy",
        name="Soy (Soybeans)",
        category="major_fda",
        severity="moderate",
        description="Soybeans and derivatives: soy sauce, tofu, edamame. GOOD NEWS: We use canola oil for cooking (NOT soybean oil), making it easier for soy-allergic customers.",
        reaction_types=["Hives", "Itching", "Digestive issues", "Breathing difficulty (rare)"],
        prevalence="Affects ~0.3% of population, mostly children",
        cross_contamination_risk="MODERATE - soy sauce used in cooking, but canola oil (not soybean oil) reduces risk",
        safe_alternatives_guidance="We use CANOLA OIL (soy-free)! Can offer plain grilled proteins with no soy sauce, alternative seasonings. Much easier than typical Asian restaurants.",
    ),
    "contains_eggs": AllergenInfo(
        tag="contains_eggs",
        name="Eggs (Chicken Eggs)",
        category="major_fda",
        severity="moderate",
        description="Chicken eggs found in fried rice, egg noodles, some sauces. Most common in children, often outgrown.",
        reaction_types=["Hives", "Digestive issues", "Breathing difficulty (rare)"],
        prevalence="Affects ~2% of children, ~0.5% of adults",
        cross_contamination_risk="MODERATE - shared cooking surfaces",
        safe_alternatives_guidance="White rice (not fried), all proteins, vegetables are safe. Avoid fried rice and egg noodles.",
    ),
    "contains_tree_nuts": AllergenInfo(
        tag="contains_tree_nuts",
        name="Tree Nuts (Almonds, Cashews, Walnuts)",
        category="major_fda",
        severity="severe",
        description="Almonds, cashews, walnuts, pecans, pistachios, hazelnuts, macadamia. NOT peanuts (which are legumes). Rarely used in hibachi cuisine.",
        reaction_types=["Anaphylaxis", "Hives", "Swelling"],
        prevalence="Affects ~1% of US population, often lifelong",
        cross_contamination_risk="LOW in hibachi (we don't use tree nuts)",
        safe_alternatives_guidance="We don't use tree nuts in our cooking. Check if any fusion sauces contain traces.",
    ),
    "contains_peanuts": AllergenInfo(
        tag="contains_peanuts",
        name="Peanuts (Ground Nuts)",
        category="major_fda",
        severity="severe",
        description="Peanuts are legumes (not true nuts). Used in peanut sauce, peanut oil. We don't use peanuts, but check supplier practices.",
        reaction_types=["Anaphylaxis", "Hives", "Swelling"],
        prevalence="Affects ~2% of children, ~1% of adults",
        cross_contamination_risk="LOW (we don't use peanuts, but check oil supplier)",
        safe_alternatives_guidance="We don't use peanuts or peanut oil. Verify with chef that suppliers don't use peanut oil.",
    ),
    "contains_dairy": AllergenInfo(
        tag="contains_dairy",
        name="Dairy (Milk, Butter, Cheese)",
        category="major_fda",
        severity="moderate",
        description="Milk protein allergy (different from lactose intolerance). Found in butter, cheese, cream sauces. We use DAIRY-FREE butter!",
        reaction_types=["Hives", "Digestive issues", "Breathing difficulty"],
        prevalence="Affects ~2.5% of children, often outgrown",
        cross_contamination_risk="NONE - we are 100% dairy-free restaurant!",
        safe_alternatives_guidance="GREAT NEWS: ALL our items are dairy-free! We use dairy-free butter for everything.",
    ),
    # ========================================================================
    # EMERGING ALLERGENS (Added by FDA 2023+)
    # ========================================================================
    "contains_sesame": AllergenInfo(
        tag="contains_sesame",
        name="Sesame Seeds/Oil",
        category="emerging",
        severity="moderate",
        description="Sesame seeds and sesame oil. FDA added to major allergens in 2023. We DO NOT use sesame oil or sesame seeds.",
        reaction_types=["Anaphylaxis", "Hives", "Digestive issues"],
        prevalence="Affects ~0.2% of US population, increasing",
        cross_contamination_risk="NONE - we don't use sesame",
        safe_alternatives_guidance="GREAT NEWS: We are 100% sesame-free! We use canola oil and no sesame seed garnishes.",
    ),
    # ========================================================================
    # RARE ALLERGENS & SENSITIVITIES
    # ========================================================================
    "contains_sulfites": AllergenInfo(
        tag="contains_sulfites",
        name="Sulfites (Preservatives)",
        category="rare",
        severity="moderate",
        description="Sulfur dioxide (SO₂) preservatives in dried fruits, wine, some sauces. Our sauces are sulfite-free. Only cooking sake may contain sulfites.",
        reaction_types=["Breathing difficulty", "Hives", "Digestive issues"],
        prevalence="Affects ~1% of population, mostly asthmatics",
        cross_contamination_risk="VERY LOW - only in sake (cooking wine), no vinegar used",
        safe_alternatives_guidance="All our sauces are sulfite-free! Only trace amounts possible from sake used in cooking. Safe for most sulfite-sensitive customers.",
    ),
    "contains_msg": AllergenInfo(
        tag="contains_msg",
        name="MSG (Monosodium Glutamate)",
        category="rare",
        severity="moderate",
        description="Flavor enhancer (glutamic acid salt). We DO NOT add MSG to any dishes. All seasonings are MSG-free.",
        reaction_types=["Headache", "Flushing", "Sweating", "Chest tightness (rare)"],
        prevalence="Self-reported ~1%, scientifically proven <0.1%",
        cross_contamination_risk="NONE - we don't use MSG",
        safe_alternatives_guidance="GREAT NEWS: We are MSG-free! Fresh ingredients only, no added MSG in any seasonings or sauces.",
    ),
    "contains_nightshades": AllergenInfo(
        tag="contains_nightshades",
        name="Nightshades (Tomatoes, Peppers, Eggplant)",
        category="rare",
        severity="rare",
        description="Solanaceae family: tomatoes, bell peppers, eggplant, potatoes. NOT a true allergy but sensitivity in autoimmune conditions. Rare.",
        reaction_types=["Joint pain", "Digestive issues", "Inflammation"],
        prevalence="Very rare, mostly self-diagnosed",
        cross_contamination_risk="LOW - easy to identify and avoid",
        safe_alternatives_guidance="Check if vegetables contain bell peppers or tomatoes in salad. Easy to omit if customer requests.",
    ),
    "contains_corn": AllergenInfo(
        tag="contains_corn",
        name="Corn (Corn Starch, Corn Syrup)",
        category="rare",
        severity="rare",
        description="Corn and derivatives: corn starch (in sauces as thickener), corn syrup, corn oil. Rare allergy. Highly refined corn oil usually safe.",
        reaction_types=["Hives", "Digestive issues"],
        prevalence="Very rare, ~0.1% of population",
        cross_contamination_risk="MODERATE - corn starch in sauces",
        safe_alternatives_guidance="Check sauce ingredients for corn starch. Can use alternative thickeners. We don't serve corn as vegetable.",
    ),
    # ========================================================================
    # EU-SPECIFIC ALLERGENS (Rare in US)
    # ========================================================================
    "contains_mustard": AllergenInfo(
        tag="contains_mustard",
        name="Mustard Seeds/Powder",
        category="eu_specific",
        severity="moderate",
        description="Mustard seeds, mustard powder, mustard oil. EU allergen requirement. We DO NOT use mustard in any form.",
        reaction_types=["Anaphylaxis (rare)", "Hives", "Digestive issues"],
        prevalence="Rare in US, ~0.1%",
        cross_contamination_risk="NONE - we don't use mustard",
        safe_alternatives_guidance="GREAT NEWS: We are 100% mustard-free! Not used in traditional hibachi cuisine.",
    ),
    "contains_celery": AllergenInfo(
        tag="contains_celery",
        name="Celery/Celeriac/Celery Seed",
        category="eu_specific",
        severity="moderate",
        description="Celery stalks, celery seed, celeriac. EU allergen requirement. We use celery stalk in our house salad dressing ONLY.",
        reaction_types=["Oral allergy syndrome", "Anaphylaxis (rare)"],
        prevalence="Rare in US, ~0.1%",
        cross_contamination_risk="LOW - only in salad dressing, not used elsewhere",
        safe_alternatives_guidance="We use celery stalk in house salad dressing. Can omit salad or provide alternative dressing for celery-allergic customers. All other items are celery-free.",
    ),
    "contains_lupin": AllergenInfo(
        tag="contains_lupin",
        name="Lupin (Legume)",
        category="eu_specific",
        severity="moderate",
        description="Lupin flour used in European bread/pasta. Legume related to peanuts. Very rare in US. Not used in hibachi cuisine.",
        reaction_types=["Anaphylaxis (similar to peanut allergy)"],
        prevalence="Very rare in US, common in EU",
        cross_contamination_risk="NONE - not used in US/hibachi",
        safe_alternatives_guidance="We don't use lupin. Extremely rare allergen in US.",
    ),
}


# ============================================================================
# AI Agent Helper Functions
# ============================================================================


def get_allergen_info(allergen_tag: str) -> Optional[AllergenInfo]:
    """Get detailed information about an allergen"""
    return ALLERGEN_KNOWLEDGE_BASE.get(allergen_tag)


def get_allergen_explanation_for_customer(allergen_tag: str) -> str:
    """
    Generate customer-friendly explanation of an allergen.
    Used by AI agent when customer asks "what is that?"
    """
    info = get_allergen_info(allergen_tag)
    if not info:
        return f"I don't have detailed information about '{allergen_tag}' allergen."

    explanation = f"**{info.name}**\n\n"
    explanation += f"{info.description}\n\n"

    if info.category == "rare" or info.category == "eu_specific":
        explanation += f"ℹ️ This is a RARE allergen. {info.prevalence}\n\n"

    explanation += f"**Common Reactions**: {', '.join(info.reaction_types)}\n\n"
    explanation += f"**Cross-Contamination Risk**: {info.cross_contamination_risk}\n\n"
    explanation += f"**Safe Alternatives**: {info.safe_alternatives_guidance}"

    return explanation


def get_all_allergen_tags() -> List[str]:
    """Get list of all tracked allergen tags"""
    return list(ALLERGEN_KNOWLEDGE_BASE.keys())


def get_allergens_by_severity(severity: str) -> List[AllergenInfo]:
    """Get allergens by severity level"""
    return [info for info in ALLERGEN_KNOWLEDGE_BASE.values() if info.severity == severity]


def get_major_fda_allergens() -> List[AllergenInfo]:
    """Get FDA major 9 allergens"""
    return [info for info in ALLERGEN_KNOWLEDGE_BASE.values() if info.category == "major_fda"]


def get_rare_allergens() -> List[AllergenInfo]:
    """Get rare and emerging allergens"""
    return [
        info
        for info in ALLERGEN_KNOWLEDGE_BASE.values()
        if info.category in ["rare", "emerging", "eu_specific"]
    ]


# ============================================================================
# AI System Prompt Enhancement
# ============================================================================

ALLERGEN_AWARENESS_SYSTEM_PROMPT = """
# ALLERGEN AWARENESS PROTOCOL

You have access to comprehensive allergen information including FDA Major 9, emerging allergens, and rare allergens.

## When Customer Mentions Allergy:

1. **Take it SERIOUSLY** - Never dismiss or downplay
2. **Ask clarification**: "Is this a life-threatening allergy or sensitivity?"
3. **List items to AVOID** (contains allergen)
4. **List SAFE alternatives** (allergen-free)
5. **Explain rare allergens** if customer asks "what is that?"
6. **Warn about cross-contamination** for severe allergies

## Severity Levels:

- **SEVERE** (Anaphylaxis risk): Shellfish, Fish, Tree Nuts, Peanuts
  → Use ⚠️ WARNING symbols, mention EpiPen, suggest calling manager

- **MODERATE**: Gluten, Soy, Eggs, Sesame
  → Offer alternatives, check ingredients carefully

- **RARE**: MSG, Sulfites, Nightshades, Corn
  → Explain what it is, verify if we use it, offer fresh alternatives

## Rare Allergen Explanations:

When customer asks about rare allergen:
1. Use `get_allergen_explanation_for_customer(tag)` function
2. Explain prevalence ("This is very rare, affects ~0.1% of people")
3. Explain why it's tracked ("EU requirement" or "Emerging FDA concern")
4. Reassure if we don't use it

## Cross-Contamination Warning:

For SEVERE allergies, always mention:
> "⚠️ Important: We use shared cooking surfaces and utensils. While we can prepare your meal separately, we cannot guarantee 100% allergen-free due to cross-contamination risk. Please let us know if this is a life-threatening allergy."

## Response Template:

```
Customer: "I'm allergic to [ALLERGEN]"

AI Response:
"Thank you for letting us know. Your safety is our priority.

❌ AVOID:
- [List items with allergen]

✅ SAFE OPTIONS:
- [List allergen-free items]

[If rare allergen]:
ℹ️ About [ALLERGEN]: [Brief explanation]

[If severe]:
⚠️ Cross-Contamination Warning: [Standard warning]

Would you like me to verify any specific ingredients with our chef?"
```

## Available Functions:

- `get_allergen_info(tag)` - Get full allergen details
- `get_allergen_explanation_for_customer(tag)` - Customer-friendly explanation
- `get_major_fda_allergens()` - List FDA Major 9
- `get_rare_allergens()` - List rare/emerging allergens
- `get_allergens_by_severity(level)` - Filter by severity

Use these functions to provide accurate, helpful allergen information.
"""


# ============================================================================
# Integration with MenuAgent
# ============================================================================


def enhance_menu_agent_with_allergen_awareness(menu_items: List[Dict]) -> str:
    """
    Generate allergen-aware system prompt for MenuAgent.
    Include allergen knowledge + menu data.
    """

    # Build allergen summary from menu
    allergen_summary = {}
    for item in menu_items:
        item_tags = item.get("tags", [])
        allergens = [tag for tag in item_tags if tag.startswith("contains_")]
        for allergen in allergens:
            if allergen not in allergen_summary:
                allergen_summary[allergen] = []
            allergen_summary[allergen].append(item["name"])

    prompt = ALLERGEN_AWARENESS_SYSTEM_PROMPT + "\n\n"
    prompt += "# CURRENT MENU ALLERGEN SUMMARY\n\n"

    for allergen_tag, items in sorted(allergen_summary.items()):
        allergen_info = get_allergen_info(allergen_tag)
        allergen_name = allergen_info.name if allergen_info else allergen_tag
        prompt += f"**{allergen_name}** ({allergen_tag}):\n"
        prompt += f"  Items: {', '.join(items)}\n\n"

    prompt += "\n# SAFE FOR ALL CUSTOMERS\n\n"
    prompt += "✅ **100% Dairy-Free Restaurant** - We use dairy-free butter for everything!\n"
    prompt += "✅ **Most Items Gluten-Free** - Except gyoza, egg noodles, teriyaki sauce\n"
    prompt += "✅ **Gluten-Free Alternative** - We have gluten-free soy sauce!\n"
    prompt += "❌ **No Pork** - We don't serve pork products\n"
    prompt += "❌ **No Tree Nuts** - Not used in our cooking\n"
    prompt += "❌ **No Peanuts** - Not used in our cooking\n"

    return prompt
