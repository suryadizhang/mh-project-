/**
 * FAQ Data with Dynamic Pricing Templates
 *
 * Uses {{PLACEHOLDER}} syntax for pricing values that will be
 * interpolated at runtime from the database (single source of truth)
 *
 * Available placeholders:
 * - {{ADULT_PRICE}} - Adult per-person price
 * - {{CHILD_PRICE}} - Child (6-12) per-person price
 * - {{CHILD_FREE_AGE}} - Age under which children are free
 * - {{PARTY_MINIMUM}} - Minimum party total
 * - {{FREE_TRAVEL_MILES}} - Free travel radius
 * - {{COST_PER_MILE}} - Cost per mile after free radius
 */

export type FaqItem = {
  id: string;
  question: string;
  answer: string;
  category: string;
  subcategory: string;
  tags: string[];
  confidence: 'high' | 'medium' | 'low';
  source_urls: string[];
  review_needed?: boolean;
};

export const faqs: FaqItem[] = [
  // Pricing & Minimums
  {
    id: 'base-pricing',
    question: 'How much does My Hibachi Chef cost?',
    answer:
      '${{ADULT_PRICE}} per adult (13+), ${{CHILD_PRICE}} per child (6-12), free for ages {{CHILD_FREE_AGE}} & under. ${{PARTY_MINIMUM}} party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and complimentary sake for adults 21+.',
    category: 'Pricing & Minimums',
    subcategory: 'Per‑person Rates',
    tags: ['pricing', 'adult price', 'child price', 'party minimum'],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'party-minimum',
    question: 'Is there a minimum party size?',
    answer:
      'Yes — ${{PARTY_MINIMUM}} total minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.',
    category: 'Pricing & Minimums',
    subcategory: 'Minimum Spend / Party Size',
    tags: ['minimum', 'party minimum', 'party size', 'upgrades'],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'tipping',
    question: 'Is tipping expected?',
    answer:
      'Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost. You can tip cash or via Venmo/Zelle Business.',
    category: 'Pricing & Minimums',
    subcategory: 'Gratuity & Fees',
    tags: ['tipping', '20-35%', 'cash', 'venmo', 'zelle'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'travel-fees',
    question: 'Do you charge travel fees?',
    answer:
      'First {{FREE_TRAVEL_MILES}} miles from our location are free. After that, ${{COST_PER_MILE}} per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.',
    category: 'Pricing & Minimums',
    subcategory: 'Travel Fees',
    tags: ['travel', 'free miles', 'cost per mile', 'flexible service'],
    confidence: 'high',
    source_urls: ['/menu', '/contact'],
  },

  // Menu & Upgrades
  {
    id: 'menu-options',
    question: "What's included in the hibachi menu?",
    answer:
      'Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.',
    category: 'Menu & Upgrades',
    subcategory: 'Included Items',
    tags: [
      '2 proteins',
      'chicken',
      'steak',
      'shrimp',
      'calamari',
      'tofu',
      'rice',
      'vegetables',
      'sake',
    ],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'premium-upgrades',
    question: 'What are the premium protein upgrades?',
    answer:
      'For premium protein upgrades: Salmon, Scallops, and Filet Mignon are +$5 per person, while Lobster Tail is +$15 per person. These upgrade your existing protein choices to premium options.',
    category: 'Menu & Upgrades',
    subcategory: 'Premium Upgrades',
    tags: [
      'upgrades',
      'salmon +$5',
      'scallops +$5',
      'filet +$5',
      'lobster +$15',
      'premium proteins',
    ],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'kids-menu',
    question: "What are the kids' portions and pricing?",
    answer:
      '${{CHILD_PRICE}} per child (6-12 years) — same 2-protein selection as adults. Ages {{CHILD_FREE_AGE}} & under eat free with adult purchase (1 protein, small rice portion).',
    category: 'Menu & Upgrades',
    subcategory: "Kids' Portions",
    tags: ['kids', 'child price', '6-12 years', 'free under age', '2 proteins'],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'sake-service',
    question: 'Do you serve sake and alcohol?',
    answer:
      "Yes! We provide sake for guests 21+ as part of the standard experience. We don't provide other alcohol — you're welcome to supply your own beer, wine, or cocktails.",
    category: 'Menu & Upgrades',
    subcategory: 'Add‑ons & Sides',
    tags: ['sake', 'alcohol', '21+', 'byob', 'beer', 'wine'],
    confidence: 'high',
    source_urls: ['/menu'],
  },

  // Booking & Payments
  {
    id: 'how-to-book',
    question: 'How do I book My Hibachi Chef?',
    answer:
      'Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit (refundable if canceled 48+ hours before event).',
    category: 'Booking & Payments',
    subcategory: 'How to Book',
    tags: ['booking', 'online', 'text', '48 hours', '$100 deposit', 'refundable'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'deposit-policy',
    question: "What's the deposit policy?",
    answer:
      '$100 refundable deposit secures your date and is deducted from final bill. Deposit is refundable if canceled 48+ hours before event, non-refundable within 48 hours. Remaining balance due on event date. Accept Venmo Business, Zelle Business, Cash, Credit Card.',
    category: 'Booking & Payments',
    subcategory: 'Deposits & Balance',
    tags: ['$100 deposit', 'refundable', '48 hours', 'deducted', 'final bill'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'payment-methods',
    question: 'What payment methods do you accept?',
    answer:
      'Venmo Business, Zelle Business, Cash, and Credit Card. Deposit paid online when booking. Balance due on event date or in advance.',
    category: 'Booking & Payments',
    subcategory: 'Payment Methods',
    tags: ['venmo', 'zelle', 'cash', 'credit card', 'online deposit'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'advance-booking',
    question: 'How far in advance should I book?',
    answer:
      '48 hours minimum required. For weekends and holidays, recommend 1-2 weeks ahead. Text (916) 740-8768 to check availability.',
    category: 'Booking & Payments',
    subcategory: 'Scheduling & Availability',
    tags: ['48 hours minimum', 'weekends', 'holidays', '1-2 weeks'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },

  // Travel & Service Area
  {
    id: 'service-areas',
    question: 'Where do you serve?',
    answer:
      'We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first {{FREE_TRAVEL_MILES}} miles, then ${{COST_PER_MILE}}/mile.',
    category: 'Travel & Service Area',
    subcategory: 'Coverage Radius',
    tags: ['bay area', 'sacramento', 'san jose', 'free travel miles'],
    confidence: 'high',
    source_urls: ['/contact', '/menu'],
  },
  {
    id: 'travel-distance',
    question: 'Do you travel to my city?',
    answer:
      'We serve the Bay Area, Sacramento, Central Valley, and coastal/mountain communities throughout Northern California. Text (916) 740-8768 with your zip code for confirmation.',
    category: 'Travel & Service Area',
    subcategory: 'Coverage Radius',
    tags: ['bay area', 'sacramento', 'central valley', 'zip code', 'confirmation'],
    confidence: 'high',
    source_urls: ['/contact'],
  },

  // On‑Site Setup & Requirements
  {
    id: 'space-requirements',
    question: 'What space do you need for the hibachi setup?',
    answer:
      'We need a minimum 8×6 feet clear area for our grill (dimensions: 68.3"L × 27.5"W × 41.3"H) plus access space for the chef. Requirements: level ground, outdoor space OR well-ventilated indoor area, and table access so guests can watch the show. Keep 10+ feet clearance from any flammable materials.',
    category: 'On‑Site Setup & Requirements',
    subcategory: 'Space & Ventilation',
    tags: [
      '8x6 feet',
      '68x27x41 inches',
      'level ground',
      'outdoor',
      'ventilated',
      'table access',
      'clearance',
    ],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'table-setup',
    question: 'How should I arrange tables and seating?',
    answer:
      "U-shape with chef's grill at the open end so everyone watches the show. Two 8-foot tables seat ~10 people, three 6-foot tables handle 12-15 guests.",
    category: 'On‑Site Setup & Requirements',
    subcategory: 'Table Setup',
    tags: ['u-shape', '8-foot tables', '10 people', '6-foot tables', '12-15 guests'],
    confidence: 'high',
    source_urls: [],
  },
  {
    id: 'indoor-cooking',
    question: 'Can you cook indoors?',
    answer:
      'Outdoor preferred for safety, but indoor possible with high ceilings and excellent ventilation. Must handle smoke and propane safely. Email cs@myhibachichef.com to discuss indoor requirements.',
    category: 'On‑Site Setup & Requirements',
    subcategory: 'Indoor vs Outdoor',
    tags: ['outdoor preferred', 'indoor possible', 'high ceilings', 'ventilation', 'smoke'],
    confidence: 'high',
    source_urls: [],
  },
  {
    id: 'what-to-provide',
    question: 'What do I need to provide?',
    answer:
      'You provide: tables, chairs, plates, utensils, glasses, beverages (except sake), napkins. We bring: hibachi grill, food, cooking tools, propane, safety equipment, sake.',
    category: 'On‑Site Setup & Requirements',
    subcategory: 'Tableware & Setup',
    tags: ['tables', 'chairs', 'plates', 'utensils', 'glasses', 'napkins'],
    confidence: 'high',
    source_urls: [],
  },

  // Dietary & Allergens
  {
    id: 'dietary-restrictions',
    question: 'Can you accommodate dietary restrictions?',
    answer:
      '✅ YES! We accommodate: Vegetarian, Vegan, Gluten-Free, Dairy-Free (we use dairy-free butter!), Nut-Free (100% nut-free facility!), Sesame-Free, Halal (Restaurant Depot certified), and Kosher-Friendly. 🏆 ALLERGEN ADVANTAGES: We are 100% nut-free, sesame-free, use dairy-free butter, and offer gluten-free soy sauce. Please notify us 48+ hours in advance. ⚠️ IMPORTANT: Shared cooking surfaces mean we cannot guarantee 100% allergen-free. View /allergens or email cs@myhibachichef.com for details.',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'vegetarian',
      'vegan',
      'gluten-free',
      'dairy-free',
      'halal',
      'kosher',
      'nut-free',
      'sesame-free',
      '48 hours',
      'allergens',
      'cross-contamination',
    ],
    confidence: 'high',
    source_urls: ['/book-us/', '/allergens'],
  },
  {
    id: 'allergen-list',
    question: 'What allergens are in your hibachi menu?',
    answer:
      'Our menu only contains 2 major allergens: Shellfish (shrimp, scallops, lobster) and Eggs (fried rice only). 🏆 ALLERGEN-FRIENDLY ADVANTAGES: We are 100% NUT-FREE (no peanuts, tree nuts), SESAME-FREE (no sesame oil/seeds), use DAIRY-FREE butter, and offer GLUTEN-FREE soy sauce. We use halal-certified ingredients from Restaurant Depot and do NOT use pork or cooking alcohol. ⚠️ Cross-contamination risk due to shared cooking surfaces. View full guide at /allergens.',
    category: 'Dietary & Allergens',
    subcategory: 'Shellfish & Sesame',
    tags: [
      'allergens',
      'shellfish',
      'eggs',
      'nut-free',
      'sesame-free',
      'dairy-free',
      'gluten-free option',
      'halal',
      'fda major 9',
      'cross-contamination',
    ],
    confidence: 'high',
    source_urls: ['/allergens'],
  },
  {
    id: 'allergen-friendly-facility',
    question: 'Is your facility allergen-friendly?',
    answer:
      '🏆 YES! We are proudly: 100% NUT-FREE (no peanuts or tree nuts ever), SESAME-FREE (no sesame oil or seeds), DAIRY-FREE (we use dairy-free butter), and offer GLUTEN-FREE soy sauce option. Our only major allergens are: Shellfish (shrimp, scallops, lobster - which guests can avoid) and Eggs (only in fried rice). This makes us one of the MOST allergen-friendly hibachi services available!',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'allergen-friendly',
      'nut-free',
      'sesame-free',
      'dairy-free',
      'gluten-free',
      '100% safe',
      'competitive advantage',
    ],
    confidence: 'high',
    source_urls: ['/allergens'],
  },
  {
    id: 'halal-certification',
    question: 'Is your menu halal-certified?',
    answer:
      '✅ YES! All our proteins (chicken, beef, seafood) are halal-certified through Restaurant Depot. We do NOT use pork products, and sake is served as a complementary DRINK only (never used in cooking). Our dairy-free butter and vegetable oil are halal-compliant. We are proud to serve our Muslim customers with confidence!',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'halal',
      'halal-certified',
      'restaurant depot',
      'muslim',
      'islamic dietary',
      'no pork',
      'no cooking alcohol',
    ],
    confidence: 'high',
    source_urls: ['/menu', '/allergens'],
  },
  {
    id: 'kosher-friendly',
    question: 'Can you accommodate kosher dietary requirements?',
    answer:
      '✅ KOSHER-FRIENDLY (not certified): We do NOT use pork, use dairy-free butter (no meat/dairy mixing), and offer salmon (fish with fins and scales = kosher). Our Jewish customers can choose: Chicken, Beef, Salmon, or Vegetables (avoiding shellfish). Most Conservative and Reform Jewish customers find our menu very accommodating. For strictly Orthodox kosher certification, we would need rabbi approval and cannot guarantee due to our shellfish offerings.',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'kosher',
      'kosher-friendly',
      'jewish',
      'no pork',
      'dairy-free',
      'salmon',
      'fins and scales',
      'accommodating',
    ],
    confidence: 'high',
    source_urls: ['/menu', '/allergens'],
  },
  {
    id: 'dairy-free-menu',
    question: 'Is your menu dairy-free?',
    answer:
      '✅ YES! We use DAIRY-FREE butter for all cooking. This means our chicken, steak, seafood, and vegetables are naturally dairy-free. Perfect for lactose intolerant guests, paleo diets, and vegan customers. Only our fried rice contains eggs (no dairy). This is a MAJOR advantage over typical hibachi restaurants that use regular butter.',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'dairy-free',
      'lactose intolerant',
      'no dairy',
      'dairy-free butter',
      'vegan option',
      'paleo',
    ],
    confidence: 'high',
    source_urls: ['/menu', '/allergens'],
  },
  {
    id: 'nut-free-facility',
    question: 'Are you a nut-free facility?',
    answer:
      '✅ 100% NUT-FREE! We do NOT use peanuts, tree nuts, or any nut products in our cooking, sauces, or ingredients. This makes us SAFE for severe nut allergy customers. We use canola oil for cooking (nut-free). ⚠️ However, we still use shared cooking surfaces, so please contact us for severe allergy protocols: cs@myhibachichef.com or (916) 740-8768.',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: [
      'nut-free',
      '100% nut-free',
      'peanut-free',
      'tree nut-free',
      'severe allergies',
      'safe',
      'canola oil',
    ],
    confidence: 'high',
    source_urls: ['/allergens'],
  },
  {
    id: 'gluten-free-options',
    question: 'Do you have gluten-free options?',
    answer:
      '✅ YES! We offer GLUTEN-FREE soy sauce as an option. All our proteins (chicken, steak, seafood, tofu) are naturally gluten-free when cooked without regular soy sauce. Vegetables, salads, and rice are gluten-free. ⚠️ Items to avoid for celiac: Gyoza (contains wheat), yakisoba noodles (wheat), and regular teriyaki sauce (contains wheat-based soy sauce). Request gluten-free soy sauce when booking!',
    category: 'Dietary & Allergens',
    subcategory: 'Gluten-Free',
    tags: ['gluten-free', 'celiac', 'gluten-free soy sauce', 'wheat-free', 'gf options'],
    confidence: 'high',
    source_urls: ['/menu', '/allergens'],
  },
  {
    id: 'cross-contamination',
    question: 'Can you guarantee allergen-free cooking?',
    answer:
      'No. We use shared cooking surfaces (hibachi grill), shared utensils, and shared oil for all cooking. While we take precautions to accommodate dietary restrictions, we CANNOT GUARANTEE a 100% allergen-free environment. Airborne particles from shellfish, fish, and soy sauce may be present. If you have severe allergies, please contact us before booking to discuss safety protocols: cs@myhibachichef.com or (916) 740-8768.',
    category: 'Dietary & Allergens',
    subcategory: 'Cross‑Contact',
    tags: [
      'cross-contamination',
      'shared surfaces',
      'allergen-free',
      'severe allergies',
      'safety protocols',
    ],
    confidence: 'high',
    source_urls: ['/allergens'],
  },
  {
    id: 'menu-change-deadline',
    question: 'Can I change my menu close to the event date?',
    answer:
      'Menu changes are NOT allowed within 12 hours of your event. We prepare fresh ingredients specifically for your party based on your menu selections. Please finalize your menu at least 12 hours before your event date to ensure we have proper ingredients prepared.',
    category: 'Booking & Payments',
    subcategory: 'Modifying a Booking',
    tags: ['menu changes', '12 hours', 'deadline', 'fresh ingredients', 'finalize menu'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'guest-count-changes',
    question: 'When do I need to finalize my guest count?',
    answer:
      'Final guest count is required 24+ hours before your event. We prepare fresh ingredients specifically for your party size, so accurate guest counts ensure proper portions. If your guest count changes significantly within 24 hours, contact us immediately at (916) 740-8768 and we will do our best to accommodate, but this cannot be guaranteed.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Cancellation & Changes',
    tags: ['guest count', '24 hours', 'finalize', 'party size', 'changes', 'fresh ingredients'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'food-refund-policy',
    question: 'Can I get a refund for leftover or uneaten food?',
    answer:
      'No refund for ordered food. We cannot keep food that has been out of refrigeration for more than 4 hours due to food safety regulations. Once we prepare and bring your ingredients to the event, those costs are non-refundable even if the food is not consumed.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Refunds & Credits',
    tags: ['food refund', 'no refund', 'food safety', '4 hours', 'leftovers', 'uneaten food'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'reschedule-timing',
    question: 'When can I reschedule my event for free?',
    answer:
      'One free reschedule is allowed if requested 24+ hours before your event. This gives us time to adjust our chef schedule and ingredient preparation. Reschedules requested within 24 hours of the event or additional reschedules cost $200. This covers our preparation costs and chef scheduling.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Cancellation & Changes',
    tags: ['reschedule', 'free reschedule', '24 hours', '$200 fee', 'chef schedule'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },

  // Policies (Cancellation, Weather, Refunds)
  {
    id: 'cancellation-policy',
    question: "What's your cancellation policy?",
    answer:
      '$100 deposit is refundable if canceled 48+ hours before event, non-refundable within 48 hours. One free reschedule allowed if requested 24+ hours before event; additional reschedules cost $200. Menu changes not allowed within 12 hours of event. No refund for ordered food as we cannot keep food out of refrigeration for more than 4 hours.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Cancellation & Changes',
    tags: [
      '48 hours',
      'deposit refundable',
      'free reschedule',
      '24 hours',
      '$200 fee',
      'menu changes',
      '12 hours',
      'food safety',
    ],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'weather-policy',
    question: 'What happens if it rains?',
    answer:
      'You must provide overhead covering (tent, patio, garage) for rain cooking. We cannot cook in unsafe/uncovered conditions. No refund for uncovered rain setups — plan a backup covered area!',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Weather / Backup Plan',
    tags: ['rain', 'overhead covering', 'tent', 'patio', 'garage', 'no refund'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },

  // Kids & Special Occasions
  {
    id: 'birthday-parties',
    question: 'Do you do birthday parties and special events?',
    answer:
      'Absolutely! Birthday parties are our specialty. Chefs make the show extra fun and family-friendly, accommodate dietary needs, and make the birthday person feel special. Book 48+ hours ahead!',
    category: 'Kids & Special Occasions',
    subcategory: 'Birthdays/Anniversaries',
    tags: ['birthday', 'special events', 'family-friendly', 'dietary needs', '48 hours'],
    confidence: 'high',
    source_urls: [],
  },

  // Contact & Response Times
  {
    id: 'contact-methods',
    question: "What's the fastest way to reach you?",
    answer:
      'Text (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Follow @my_hibachi_chef on Instagram and Facebook. Usually respond within 1-2 hours during business hours.',
    category: 'Contact & Response Times',
    subcategory: 'Best Way to Reach',
    tags: ['text', '916-740-8768', 'email', 'instagram', 'facebook', '1-2 hours'],
    confidence: 'high',
    source_urls: ['/contact'],
  },

  // Additional Popular Questions Based on Competitor Analysis
  {
    id: 'extra-protein',
    question: 'Can I add an extra protein or more?',
    answer:
      'Yes! Each guest normally gets 2 proteins, but you can add an extra protein for +$10 each. This is an additional option that gives you more food, not an upgrade. If you want the extra protein to be a premium option (Salmon, Scallops, Filet Mignon, or Lobster Tail), that would be the +$10 for the additional protein plus the premium upgrade cost (+$5 for Salmon/Scallops/Filet Mignon, +$15 for Lobster Tail). Contact us at cs@myhibachichef.com to customize your menu.',
    category: 'Menu & Upgrades',
    subcategory: 'Add‑ons & Sides',
    tags: ['extra protein', 'additional protein', 'add-on', '+$10', 'more food'],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'additional-enhancements',
    question: 'What additional enhancements can I add to my menu?',
    answer:
      'We offer several delicious add-on options: Yakisoba Noodles (Japanese-style lo mein), Extra Fried Rice, Extra Vegetables (mixed seasonal vegetables), and Edamame (steamed soybeans with sea salt) are all +$5 each. Gyoza (pan-fried Japanese dumplings) and Extra Protein (add additional proteins to your meal) are +$10 each. These can be ordered per person or shared family-style.',
    category: 'Menu & Upgrades',
    subcategory: 'Add‑ons & Sides',
    tags: [
      'enhancements',
      'add-ons',
      'yakisoba noodles +$5',
      'extra rice +$5',
      'extra vegetables +$5',
      'edamame +$5',
      'gyoza +$10',
      'extra protein +$10',
      'sides',
    ],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'chef-arrival-time',
    question: 'What time will the chef arrive?',
    answer:
      "Our chef will arrive approximately 15-30 minutes before your scheduled party time for setup. Setup is quick and usually takes just a few minutes. We'll confirm arrival time when we call to finalize details.",
    category: 'On-Site Setup & Requirements',
    subcategory: 'General',
    tags: ['arrival time', '15-30 minutes early', 'setup time'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'service-duration',
    question: 'How long does the hibachi experience last?',
    answer:
      'Standard service is approximately 90 minutes, which includes setup, the full hibachi cooking show and meal service, and cleanup. For larger parties (20+ guests), service may extend up to 2-2.5 hours. Additional time is available upon request for an extra fee. Contact us to discuss timing for your specific event.',
    category: 'On-Site Setup & Requirements',
    subcategory: 'General',
    tags: ['service duration', '90 minutes', 'how long', 'time', 'cooking show', 'large parties'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'protein-choices-different',
    question: 'Can guests choose different proteins?',
    answer:
      'Absolutely! Each guest can choose their own 2 proteins from: Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu. Everyone can have different selections. Premium upgrades (Filet Mignon +$5, Lobster Tail +$15) are also individual choices.',
    category: 'Menu & Upgrades',
    subcategory: 'Included Items',
    tags: ['individual choices', 'different proteins', 'personalized'],
    confidence: 'high',
    source_urls: ['/menu'],
  },
  {
    id: 'why-deposit-required',
    question: 'Why is a deposit required?',
    answer:
      'The $100 deposit confirms your reservation and helps us prepare fresh ingredients specifically for your party. It also ensures commitment from both sides and covers our preparation costs. The deposit is deducted from your final bill on party day.',
    category: 'Booking & Payments',
    subcategory: 'Deposits & Balance',
    tags: ['deposit explanation', 'reservation confirmation', 'preparation costs'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'safety-precautions',
    question: 'Is it safe to use propane for cooking in residential areas?',
    answer:
      'Yes, absolutely safe! Our chefs are experienced professionals who follow strict safety protocols. We bring portable fire extinguishers to every event, perform propane leak checks, maintain safe distances from flammable objects, and ensure proper ventilation.',
    category: 'On-Site Setup & Requirements',
    subcategory: 'General',
    tags: ['safety', 'propane', 'fire extinguisher', 'leak checks', 'protocols'],
    confidence: 'high',
    source_urls: [],
  },
  {
    id: 'receipt-invoice',
    question: 'Can I get a receipt or invoice?',
    answer:
      'Yes! We can provide receipts or invoices for deposit, remaining balance, and gratuity. Perfect for expense reimbursement or business events. Contact cs@myhibachichef.com to request documentation.',
    category: 'Booking & Payments',
    subcategory: 'Deposits & Balance',
    tags: ['receipt', 'invoice', 'business', 'expense reimbursement'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },

  // Food Safety & Illness Prevention
  {
    id: 'food-safety-policy',
    question: 'What are your food safety standards?',
    answer:
      'Our chefs follow strict food safety protocols: proteins are cooked to FDA-recommended internal temperatures (165°F+ for poultry, 145°F+ for beef/seafood), ingredients are transported in temperature-controlled coolers, and we maintain proper hygiene throughout service. The hibachi grill reaches 400°F+, ensuring thorough cooking. For any food safety concerns, please report within 72 hours to cs@myhibachichef.com. Customer is responsible for proper storage of any leftovers after our chef departs.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Food Safety',
    tags: [
      'food safety',
      'FDA',
      'temperature',
      'cooking standards',
      'hygiene',
      'claims',
      'leftovers',
    ],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'norovirus-clarification',
    question: 'What if multiple guests get sick after an event?',
    answer:
      'Norovirus ("stomach flu") spreads person-to-person through direct contact, NOT through properly cooked food. Our hibachi grill reaches 400°F+, which kills all foodborne pathogens. If multiple guests develop vomiting/diarrhea 12-48 hours after an event, it is statistically more likely that an already-infected guest attended and transmitted the virus to others through contact. This is a common occurrence at gatherings where people share food, utensils, and close spaces.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Food Safety',
    tags: [
      'norovirus',
      'stomach flu',
      'illness',
      'transmission',
      'person-to-person',
      'cooked food',
    ],
    confidence: 'high',
    source_urls: [],
  },
  {
    id: 'pre-event-health-notice',
    question: 'What if a guest is feeling unwell before the event?',
    answer:
      '⚠️ IMPORTANT: To protect all guests, anyone who has experienced vomiting, diarrhea, or fever within the past 48 hours should NOT attend the event. Norovirus and other stomach bugs spread extremely easily at gatherings. If you need to reschedule due to illness, we offer flexible options—just contact us. Attending while sick puts other guests at risk of infection.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Food Safety',
    tags: ['illness', 'sick', 'unwell', 'vomiting', 'fever', 'reschedule', 'contagious'],
    confidence: 'high',
    source_urls: ['/book-us/'],
  },
  {
    id: 'leftover-food-storage',
    question: 'How should I store leftover hibachi food?',
    answer:
      'Refrigerate all leftovers within 2 hours of service completion to prevent bacterial growth. Store at 40°F or below and consume within 3-4 days. My Hibachi is not responsible for illness resulting from improperly stored leftovers after our chef departs.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Food Safety',
    tags: ['leftovers', 'storage', 'refrigerate', 'food safety', '2 hours', 'bacterial growth'],
    confidence: 'high',
    source_urls: [],
  },
];

export const categories = [
  'Pricing & Minimums',
  'Menu & Upgrades',
  'Booking & Payments',
  'Travel & Service Area',
  'On‑Site Setup & Requirements',
  'Dietary & Allergens',
  'Policies (Cancellation, Weather, Refunds)',
  'Kids & Special Occasions',
  'Corporate & Insurance',
  'Contact & Response Times',
];

// Subcategory mapping
export const subcategories = {
  'Pricing & Minimums': [
    'Per‑person Rates',
    'Minimum Spend / Party Size',
    'Gratuity & Fees',
    'Travel Fees',
    'Discounts / Group Rates',
  ],
  'Menu & Upgrades': [
    'Included Items',
    'Protein Choices',
    'Premium Upgrades',
    'Add‑ons & Sides',
    "Kids' Portions",
  ],
  'Booking & Payments': [
    'How to Book',
    'Deposits & Balance',
    'Payment Methods',
    'Scheduling & Availability',
    'Modifying a Booking',
  ],
  'Travel & Service Area': ['Coverage Radius', 'Travel Fees', 'Multi‑stop / Venue Rules'],
  'On‑Site Setup & Requirements': [
    'Space & Ventilation',
    'Power/Propane & Safety',
    'Tableware & Setup',
    'Indoor vs Outdoor',
  ],
  'Dietary & Allergens': [
    'Gluten‑Free',
    'Vegetarian/Vegan',
    'Shellfish & Sesame',
    'Cross‑Contact',
    'Dietary Accommodations',
  ],
  'Policies (Cancellation, Weather, Refunds)': [
    'Cancellation & Changes',
    'Weather / Backup Plan',
    'Refunds & Credits',
    'Late / No‑Show',
    'Food Safety',
  ],
  'Kids & Special Occasions': [
    'Children Pricing & Portions',
    'Birthdays/Anniversaries',
    'Weddings / Corporate Milestones',
  ],
  'Corporate & Insurance': ['W‑9 / Vendor Setup', 'COI / Liability Coverage', 'Tax & Invoicing'],
  'Contact & Response Times': ['Best Way to Reach', 'Response SLAs', 'After‑hours / Weekends'],
};

// Generate all tags dynamically from the FAQ data
export const getAllTags = () => Array.from(new Set(faqs.flatMap((faq) => faq.tags || []))).sort();

// Pre-computed tags for better performance
export const allTags = [
  'pricing',
  'cost',
  'adults',
  'children',
  'minimum',
  'travel',
  'fees',
  'distance',
  'miles',
  'party size',
  'guests',
  'tipping',
  'gratuity',
  'chef',
  'menu',
  'proteins',
  'included',
  'sake',
  'upgrades',
  'filet',
  'lobster',
  'premium',
  'yakisoba',
  'noodles',
  'edamame',
  'gyoza',
  'enhancements',
  'dietary',
  'allergies',
  'vegetarian',
  'vegan',
  'gluten-free',
  'kids',
  'family',
  'alcohol',
  '21+',
  'beverages',
  'booking',
  'reserve',
  'advance',
  'deposit',
  'payment',
  'refundable',
  'venmo',
  'zelle',
  'cash',
  'credit card',
  '48 hours',
  'availability',
  'service area',
  'bay area',
  'sacramento',
  'coverage',
  'space',
  'grill',
  'dimensions',
  'setup',
  'tables',
  'seating',
  'arrangement',
  'u-shape',
  'indoor',
  'outdoor',
  'ventilation',
  'safety',
  'host provides',
  'chef brings',
  'requirements',
  'cancellation',
  'refund',
  '7 days',
  'reschedule',
  'weather',
  'rain',
  'covered area',
  'tent',
  'birthday',
  'kids party',
  'family friendly',
  'contact',
  'phone',
  'email',
  'social media',
];
