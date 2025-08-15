export type FaqItem = {
  id: string;
  question: string;
  answer: string;
  category: string;
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
    answer: '$55 per adult, $30 per child (6-12 years), and children 5 & under eat free with adult purchase. We have a $550 party minimum (approximately 10 adults). This includes your choice of 2 proteins, hibachi fried rice, vegetables, salad, sauces, and sake for adults 21+. Text us at (916) 740-8768 for a custom quote.',
    category: 'Pricing & Minimums',
    tags: ['pricing', 'cost', 'adults', 'children', 'minimum'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'travel-fees',
    question: 'Do you charge travel fees?',
    answer: 'The first 30 miles from our location are completely free. After 30 miles, it\'s $2 per mile. We serve all of Northern California with flexible options for your area. Text us at (916) 740-8768 to calculate your travel fee.',
    category: 'Pricing & Minimums',
    tags: ['travel', 'fees', 'distance', 'miles'],
    confidence: 'high',
    source_urls: ['/menu', '/contact']
  },
  {
    id: 'party-minimum',
    question: 'What\'s the minimum party size?',
    answer: 'We require a $550 minimum spend, which typically equals about 10 adults. Smaller groups can still book by reaching the minimum through additional proteins, upgrades, or add-ons. Contact us at cs@myhibachichef.com to plan your party.',
    category: 'Pricing & Minimums',
    tags: ['minimum', 'party size', 'guests'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'tipping',
    question: 'Is tipping expected?',
    answer: 'Tips are greatly appreciated and paid directly to your chef at the end of the party. We suggest 20-35% of the total service cost (base price + upgrades). You can tip in cash or via Venmo/Zelle Business. Our chefs work hard to create an unforgettable experience!',
    category: 'Pricing & Minimums',
    tags: ['tipping', 'gratuity', 'chef'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },

  // Menu & Upgrades
  {
    id: 'menu-options',
    question: 'What\'s included in the hibachi menu?',
    answer: 'Each guest chooses 2 proteins: Chicken, NY Strip Steak, Shrimp, Scallops, Salmon, or Tofu (vegetarian). Plus hibachi fried rice, fresh vegetables, side salad, signature sauces, and sake for adults 21+. Premium upgrades available: Filet Mignon (+$5) or Lobster Tail (+$15). Text us at (916) 740-8768 for the full menu.',
    category: 'Menu & Upgrades',
    tags: ['menu', 'proteins', 'included', 'sake'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'premium-upgrades',
    question: 'Can I upgrade to premium proteins?',
    answer: 'Yes! Upgrade to Filet Mignon for +$5 per person or Lobster Tail for +$15 per person. You can also add a 3rd protein for +$10 per person, or extra sides like fried rice or vegetables for +$5 each. Contact us at cs@myhibachichef.com to customize your menu.',
    category: 'Menu & Upgrades',
    tags: ['upgrades', 'filet', 'lobster', 'premium'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'dietary-restrictions',
    question: 'Can you accommodate dietary restrictions?',
    answer: 'Absolutely! We accommodate vegetarian, vegan, gluten-free, dairy-free, halal, and kosher dietary needs. Please notify us of any food allergies or restrictions at least 48 hours in advance so our chef can prepare accordingly. Email us at cs@myhibachichef.com with your specific needs.',
    category: 'Dietary & Allergens',
    tags: ['dietary', 'allergies', 'vegetarian', 'vegan', 'gluten-free'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'kids-menu',
    question: 'Do you have kid-friendly options?',
    answer: 'Yes! Children 6-12 years are $30 and get the same 2-protein selection as adults. Kids 5 & under eat free with adult purchase (1 protein, small rice portion). Our chefs love entertaining kids and can make the show extra family-friendly. Just let us know you have little ones!',
    category: 'Kids & Special Occasions',
    tags: ['kids', 'children', 'family'],
    confidence: 'high',
    source_urls: ['/menu']
  },
  {
    id: 'sake-service',
    question: 'Do you serve sake and alcohol?',
    answer: 'Yes! We provide plenty of sake for guests 21+ as part of our standard hibachi experience. We do not provide other alcoholic beverages - you\'re welcome to supply your own beer, wine, or cocktails for your party. Please drink responsibly!',
    category: 'Menu & Upgrades',
    tags: ['sake', 'alcohol', '21+', 'beverages'],
    confidence: 'high',
    source_urls: ['/menu']
  },

  // Booking & Payments
  {
    id: 'how-to-book',
    question: 'How do I book My Hibachi Chef?',
    answer: 'Book online through our website or text us at (916) 740-8768. All events must be booked at least 48 hours in advance. You\'ll need to provide event details, guest count, and pay a $100 refundable deposit to secure your date (refundable if canceled 7+ days before event). We\'ll follow up to finalize menu and details.',
    category: 'Booking & Payments',
    tags: ['booking', 'reserve', 'advance'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'deposit-policy',
    question: 'What\'s the deposit policy?',
    answer: 'We require a $100 refundable deposit to secure your booking date (refundable if canceled 7+ days before event). This deposit is deducted from your final bill. The remaining balance is due on or before your event date. We accept Venmo Business, Zelle Business, Cash, or Credit Card.',
    category: 'Booking & Payments',
    tags: ['deposit', 'payment', 'refundable'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'payment-methods',
    question: 'What payment methods do you accept?',
    answer: 'We accept Venmo Business, Zelle Business, Cash, and Credit Card. The $100 deposit can be paid online when booking. The remaining balance is due on your event date and can be paid directly to your chef or in advance by contacting us.',
    category: 'Booking & Payments',
    tags: ['payment', 'venmo', 'zelle', 'cash', 'credit card'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'advance-booking',
    question: 'How far in advance should I book?',
    answer: 'All bookings require at least 48 hours advance notice. This ensures chef availability and allows time for ingredient preparation. For popular dates (weekends, holidays), we recommend booking 1-2 weeks ahead. Text us at (916) 740-8768 to check availability.',
    category: 'Booking & Payments',
    tags: ['advance booking', '48 hours', 'availability'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },

  // Travel & Service Area
  {
    id: 'service-areas',
    question: 'Where do you serve?',
    answer: 'We serve all of Northern California with flexible options for your area. Primary areas include the San Francisco Bay Area (SF, San Jose, Oakland), Sacramento region, and surrounding cities. Free travel for first 30 miles, then $2/mile. Contact cs@myhibachichef.com for specific location confirmation.',
    category: 'Travel & Service Area',
    tags: ['service area', 'bay area', 'sacramento'],
    confidence: 'high',
    source_urls: ['/contact', '/menu']
  },
  {
    id: 'travel-distance',
    question: 'Do you travel to my city?',
    answer: 'We serve throughout Northern California with flexible options for your area. This includes the entire Bay Area, Sacramento, Central Valley, and many coastal and mountain communities. If you\'re unsure about your location, text us at (916) 740-8768 with your zip code and we\'ll confirm availability and travel fees.',
    category: 'Travel & Service Area',
    tags: ['travel', 'distance', 'coverage'],
    confidence: 'high',
    source_urls: ['/contact']
  },

  // On-Site Setup & Requirements
  {
    id: 'space-requirements',
    question: 'What space do I need for the hibachi grill?',
    answer: 'Please provide a clear area 68.3" L x 27.5" W x 41.3" H for our hibachi grill. We need level ground, outdoor space or well-ventilated indoor area, and access to tables/seating arranged so all guests can watch the cooking show. We provide all cooking equipment and ingredients.',
    category: 'On-Site Setup & Requirements',
    tags: ['space', 'grill', 'dimensions', 'setup'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'table-setup',
    question: 'How should I arrange tables and seating?',
    answer: 'Arrange tables in a U-shape with the chef\'s grill at the open end so everyone can watch the show. Two 8-foot tables seat about 10 people, three 6-foot tables handle 12-15 guests. You provide tables, chairs, plates, utensils, and drinks (except sake, which we bring).',
    category: 'On-Site Setup & Requirements',
    tags: ['tables', 'seating', 'arrangement', 'u-shape'],
    confidence: 'high',
    source_urls: []
  },
  {
    id: 'indoor-cooking',
    question: 'Can you cook indoors?',
    answer: 'We prefer outdoor cooking for safety and ventilation, but indoor events are possible with high ceilings and excellent ventilation. The space must be well-ventilated to handle smoke and propane use. Contact us at cs@myhibachichef.com to discuss your indoor venue requirements.',
    category: 'On-Site Setup & Requirements',
    tags: ['indoor', 'outdoor', 'ventilation', 'safety'],
    confidence: 'high',
    source_urls: []
  },
  {
    id: 'what-to-provide',
    question: 'What do I need to provide?',
    answer: 'You provide: tables and chairs, plates and utensils, drink glasses, beverages (except sake), and napkins. We bring: hibachi grill, all food ingredients, cooking tools, propane, safety equipment, and sake. Optional: you can also provide background music.',
    category: 'On-Site Setup & Requirements',
    tags: ['host provides', 'chef brings', 'requirements'],
    confidence: 'high',
    source_urls: []
  },

  // Policies
  {
    id: 'cancellation-policy',
    question: 'What\'s your cancellation policy?',
    answer: 'Full refund if canceled at least 7 days before your event. The $100 deposit is refundable for cancellations 7+ days before event, non-refundable within 7 days. One free reschedule allowed within 48 hours of booking; additional reschedules incur a $100 fee. Contact cs@myhibachichef.com for cancellations.',
    category: 'Policies (Cancellation, Weather, Refunds)',
    tags: ['cancellation', 'refund', '7 days', 'reschedule'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },
  {
    id: 'weather-policy',
    question: 'What happens if it rains?',
    answer: 'You must provide overhead covering (tent, patio, garage) for cooking in case of rain. We cannot cook in unsafe or completely uncovered conditions. Cancellations due to uncovered rain setups receive no refund. Plan ahead with a backup covered area!',
    category: 'Policies (Cancellation, Weather, Refunds)',
    tags: ['weather', 'rain', 'covered area', 'tent'],
    confidence: 'high',
    source_urls: ['/BookUs']
  },

  // Kids & Special Occasions
  {
    id: 'birthday-parties',
    question: 'Do you do birthday parties?',
    answer: 'Absolutely! Birthday parties are our specialty. Our chefs love entertaining kids and can make the show extra fun and family-friendly. We can accommodate special dietary needs and make the birthday person feel special. Book at least 48 hours ahead!',
    category: 'Kids & Special Occasions',
    tags: ['birthday', 'kids party', 'family friendly'],
    confidence: 'high',
    source_urls: []
  },

  // Contact & Response Times
  {
    id: 'contact-methods',
    question: 'How do I contact you?',
    answer: 'Text us at (916) 740-8768 for fastest response, or email cs@myhibachichef.com. Follow us on Instagram @my_hibachi_chef and Facebook for updates. We typically respond within a few hours during business hours and aim to confirm bookings quickly.',
    category: 'Contact & Response Times',
    tags: ['contact', 'phone', 'email', 'social media'],
    confidence: 'high',
    source_urls: ['/contact']
  }
];

export const categories = [
  'Pricing & Minimums',
  'Menu & Upgrades',
  'Booking & Payments',
  'Travel & Service Area',
  'On-Site Setup & Requirements',
  'Dietary & Allergens',
  'Policies (Cancellation, Weather, Refunds)',
  'Kids & Special Occasions',
  'Corporate & Insurance',
  'Contact & Response Times'
];

export const allTags = [
  'pricing', 'cost', 'adults', 'children', 'minimum', 'travel', 'fees', 'distance', 'miles',
  'party size', 'guests', 'tipping', 'gratuity', 'chef', 'menu', 'proteins', 'included', 'sake',
  'upgrades', 'filet', 'lobster', 'premium', 'dietary', 'allergies', 'vegetarian', 'vegan',
  'gluten-free', 'kids', 'family', 'alcohol', '21+', 'beverages', 'booking', 'reserve',
  'advance', 'deposit', 'payment', 'refundable', 'venmo', 'zelle', 'cash', 'credit card',
  '48 hours', 'availability', 'service area', 'bay area', 'sacramento', 'coverage',
  'space', 'grill', 'dimensions', 'setup', 'tables', 'seating', 'arrangement', 'u-shape',
  'indoor', 'outdoor', 'ventilation', 'safety', 'host provides', 'chef brings', 'requirements',
  'cancellation', 'refund', '7 days', 'reschedule', 'weather', 'rain', 'covered area', 'tent',
  'birthday', 'kids party', 'family friendly', 'contact', 'phone', 'email', 'social media'
];
