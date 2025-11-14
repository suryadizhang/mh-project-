export type FaqItem = {
  id: string
  question: string
  answer: string
  category: string
  subcategory: string
  tags: string[]
  confidence: 'high' | 'medium' | 'low'
  source_urls: string[]
  review_needed?: boolean
}

export const faqs: FaqItem[] = [
  // Pricing & Minimums
  {
    id: 'base-pricing',
    question: 'How much does My Hibachi Chef cost?',
    answer:
      '$55 per adult (13+), $30 per child (6-12), free for ages 5 & under. $550 party minimum (≈10 adults). This includes your choice of 2 proteins (Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu), hibachi fried rice, fresh vegetables, side salad, signature sauces, and plenty of sake for adults 21+.',
    category: 'Pricing & Minimums',
    subcategory: 'Per‑person Rates',
    tags: ['pricing', '$55 adult', '$30 child', '$550 minimum'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'party-minimum',
    question: 'Is there a minimum party size?',
    answer:
      'Yes — $550 total minimum (approximately 10 adults). Smaller groups can reach the minimum through upgrades or additional proteins.',
    category: 'Pricing & Minimums',
    subcategory: 'Minimum Spend / Party Size',
    tags: ['minimum', '$550', 'party size', 'upgrades'],
    confidence: 'high',
    source_urls: ['/menu']
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
    source_urls: ['/BookUs']
  },
  {
    id: 'travel-fees',
    question: 'Do you charge travel fees?',
    answer:
      'First 30 miles from our location are free. After that, $2 per mile with flexible options for your area. Text (916) 740-8768 to calculate your travel fee.',
    category: 'Pricing & Minimums',
    subcategory: 'Travel Fees',
    tags: ['travel', 'free 30 miles', '$2 per mile', 'flexible service'],
    confidence: 'high',
    source_urls: ['/menu', '/contact']
  },

  // Menu & Upgrades
  {
    id: 'menu-options',
    question: "What's included in the hibachi menu?",
    answer:
      'Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Calamari, or Tofu. Plus fried rice, vegetables, salad, sauces, and sake for adults 21+.',
    category: 'Menu & Upgrades',
    subcategory: 'Included Items',
    tags: ['2 proteins', 'chicken', 'steak', 'shrimp', 'calamari', 'tofu', 'rice', 'vegetables', 'sake'],
    confidence: 'high',
    source_urls: ['/menu']
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
      'premium proteins'
    ],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'kids-menu',
    question: "What are the kids' portions and pricing?",
    answer:
      '$30 per child (6-12 years) — same 2-protein selection as adults. Ages 5 & under eat free with adult purchase (1 protein, small rice portion).',
    category: 'Menu & Upgrades',
    subcategory: "Kids' Portions",
    tags: ['kids', '$30', '6-12 years', 'free under 5', '2 proteins'],
    confidence: 'high',
    source_urls: ['/menu']
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
    source_urls: ['/menu']
  },

  // Booking & Payments
  {
    id: 'how-to-book',
    question: 'How do I book My Hibachi Chef?',
    answer:
      'Book online through our website or text (916) 740-8768. Must book 48+ hours in advance. Requires event details, guest count, and $100 refundable deposit (refundable if canceled 7+ days before event).',
    category: 'Booking & Payments',
    subcategory: 'How to Book',
    tags: ['booking', 'online', 'text', '48 hours', '$100 deposit', 'refundable'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'deposit-policy',
    question: "What's the deposit policy?",
    answer:
      '$100 refundable deposit secures your date and is deducted from final bill (refundable if canceled 7+ days before event). Remaining balance due on event date. Accept Venmo Business, Zelle Business, Cash, Credit Card.',
    category: 'Booking & Payments',
    subcategory: 'Deposits & Balance',
    tags: ['$100 deposit', 'refundable', 'deducted', 'final bill'],
    confidence: 'high',
    source_urls: ['/BookUs']
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
    source_urls: ['/BookUs']
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
    source_urls: ['/BookUs']
  },

  // Travel & Service Area
  {
    id: 'service-areas',
    question: 'Where do you serve?',
    answer:
      'We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask! Free travel first 30 miles, then $2/mile.',
    category: 'Travel & Service Area',
    subcategory: 'Coverage Radius',
    tags: ['bay area', 'sacramento', 'san jose', 'free 30 miles'],
    confidence: 'high',
    source_urls: ['/contact', '/menu']
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
    source_urls: ['/contact']
  },

  // On‑Site Setup & Requirements
  {
    id: 'space-requirements',
    question: 'What space do you need for the hibachi setup?',
    answer:
      'Clear area 68.3"L × 27.5"W × 41.3"H for our grill. Need level ground, outdoor space or well-ventilated indoor area, and table access so guests can watch the show.',
    category: 'On‑Site Setup & Requirements',
    subcategory: 'Space & Ventilation',
    tags: ['68x27x41 inches', 'level ground', 'outdoor', 'ventilated', 'table access'],
    confidence: 'high',
    source_urls: ['/BookUs']
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
    source_urls: []
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
    source_urls: []
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
    source_urls: []
  },

  // Dietary & Allergens
  {
    id: 'dietary-restrictions',
    question: 'Can you accommodate dietary restrictions?',
    answer:
      'Yes! Vegetarian, vegan, gluten-free, dairy-free, halal, kosher. Please notify us 48+ hours in advance so our chef can prepare. Email cs@myhibachichef.com with specific needs.',
    category: 'Dietary & Allergens',
    subcategory: 'Dietary Accommodations',
    tags: ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'halal', 'kosher', '48 hours'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },

  // Policies (Cancellation, Weather, Refunds)
  {
    id: 'cancellation-policy',
    question: "What's your cancellation policy?",
    answer:
      'Full refund if canceled 7+ days before event. $100 deposit is refundable for cancellations 7+ days before event, non-refundable within 7 days. One free reschedule within 48 hours of booking; additional reschedules cost $100.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    subcategory: 'Cancellation & Changes',
    tags: ['7 days', 'full refund', 'deposit refundable', 'free reschedule', '$100 fee'],
    confidence: 'high',
    source_urls: ['/BookUs']
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
    source_urls: ['/BookUs']
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
    source_urls: []
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
    source_urls: ['/contact']
  },

  // Additional Popular Questions Based on Competitor Analysis
  {
    id: 'third-protein',
    question: 'Can I add a third protein or more?',
    answer:
      'Yes! Each guest normally gets 2 proteins, but you can add a 3rd protein for +$10 per person. This is an additional option that gives you more food, not an upgrade. If you want the 3rd protein to be a premium option (Filet Mignon or Lobster Tail), that would be the +$10 for the additional protein plus the premium upgrade cost. Contact us at cs@myhibachichef.com to customize your menu.',
    category: 'Menu & Upgrades',
    subcategory: 'Add‑ons & Sides',
    tags: ['third protein', 'additional protein', 'add-on', '+$10', 'more food'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'additional-enhancements',
    question: 'What additional enhancements can I add to my menu?',
    answer:
      'We offer several delicious add-on options: Yakisoba Noodles (Japanese-style lo mein), Extra Fried Rice, Extra Vegetables (mixed seasonal vegetables), and Edamame (steamed soybeans with sea salt) are all +$5 each. Gyoza (pan-fried Japanese dumplings) and 3rd Protein (add a third protein to your meal) are +$10 each. These can be ordered per person or shared family-style.',
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
      '3rd protein +$10',
      'sides'
    ],
    confidence: 'high',
    source_urls: ['/menu']
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
    source_urls: ['/BookUs']
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
    source_urls: ['/menu']
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
    source_urls: ['/BookUs']
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
    source_urls: []
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
    source_urls: ['/BookUs']
  }
]

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
  'Contact & Response Times'
]

// Subcategory mapping
export const subcategories = {
  'Pricing & Minimums': [
    'Per‑person Rates',
    'Minimum Spend / Party Size',
    'Gratuity & Fees',
    'Travel Fees',
    'Discounts / Group Rates'
  ],
  'Menu & Upgrades': [
    'Included Items',
    'Protein Choices',
    'Premium Upgrades',
    'Add‑ons & Sides',
    "Kids' Portions"
  ],
  'Booking & Payments': [
    'How to Book',
    'Deposits & Balance',
    'Payment Methods',
    'Scheduling & Availability',
    'Modifying a Booking'
  ],
  'Travel & Service Area': ['Coverage Radius', 'Travel Fees', 'Multi‑stop / Venue Rules'],
  'On‑Site Setup & Requirements': [
    'Space & Ventilation',
    'Power/Propane & Safety',
    'Tableware & Setup',
    'Indoor vs Outdoor'
  ],
  'Dietary & Allergens': [
    'Gluten‑Free',
    'Vegetarian/Vegan',
    'Shellfish & Sesame',
    'Cross‑Contact',
    'Dietary Accommodations'
  ],
  'Policies (Cancellation, Weather, Refunds)': [
    'Cancellation & Changes',
    'Weather / Backup Plan',
    'Refunds & Credits',
    'Late / No‑Show'
  ],
  'Kids & Special Occasions': [
    'Children Pricing & Portions',
    'Birthdays/Anniversaries',
    'Weddings / Corporate Milestones'
  ],
  'Corporate & Insurance': ['W‑9 / Vendor Setup', 'COI / Liability Coverage', 'Tax & Invoicing'],
  'Contact & Response Times': ['Best Way to Reach', 'Response SLAs', 'After‑hours / Weekends']
}

// Generate all tags dynamically from the FAQ data
export const getAllTags = () => Array.from(new Set(faqs.flatMap(faq => faq.tags || []))).sort()

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
  'social media'
]
