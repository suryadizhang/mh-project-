export const menuData = {
  hero: {
    title: 'Premium Hibachi Menu',
    subtitle:
      'Experience authentic Japanese hibachi dining in the comfort of your home',
    valueProposition: [
      { icon: '🚚', text: 'We Come to You' },
      { icon: '👨‍🍳', text: 'Professional Chef' },
      { icon: '🎭', text: 'Live Entertainment' },
    ],
    features: [
      {
        icon: '⭐',
        title: 'Premium Quality',
        subtitle: 'Fresh ingredients',
      },
      {
        icon: '🔧',
        title: 'Custom Experience',
        subtitle: 'Tailored to you',
      },
      {
        icon: '💎',
        title: 'Luxury Service',
        subtitle: 'Premium quality',
      },
    ],
  },

  pricing: {
    title: 'Transparent Pricing',
    subtitle: 'Premium experience, honest pricing — no hidden fees',
    tiers: [
      {
        id: 'basic',
        name: 'Essential Hibachi',
        price: '$35',
        description: 'Perfect for intimate gatherings',
        minGuests: 6,
        features: [
          'Professional hibachi chef',
          'All cooking equipment provided',
          'Choice of 2 proteins',
          'Fried rice and vegetables',
          'Entertaining cooking show',
        ],
      },
      {
        id: 'premium',
        name: 'Signature Experience',
        price: '$45',
        description: 'Our most popular package',
        minGuests: 8,
        popular: true,
        features: [
          'Everything in Essential',
          'Choice of 3 premium proteins',
          'Hibachi noodles included',
          'Appetizer (soup or salad)',
          'Extended entertainment show',
        ],
      },
      {
        id: 'luxury',
        name: 'Ultimate Hibachi',
        price: '$65',
        description: 'The complete luxury experience',
        minGuests: 10,
        features: [
          'Everything in Signature',
          'Premium protein selections',
          'Multiple appetizers',
          'Special sauces & seasonings',
          'Extended performance with tricks',
        ],
      },
    ],
  },

  proteins: {
    title: 'Premium Protein Selection',
    subtitle: 'Choose from our selection of fresh, high-quality proteins',
    categories: [
      {
        name: 'Poultry',
        items: [
          {
            name: 'Chicken Breast',
            description: 'Tender, juicy chicken breast',
          },
          { name: 'Chicken Thighs', description: 'Flavorful dark meat' },
        ],
      },
      {
        name: 'Beef',
        items: [
          { name: 'Sirloin Steak', description: 'Premium cut sirloin' },
          { name: 'Ribeye', description: 'Marbled, tender ribeye' },
          { name: 'Filet Mignon', description: 'Premium tenderloin' },
        ],
      },
      {
        name: 'Seafood',
        items: [
          { name: 'Shrimp', description: 'Large, fresh shrimp' },
          { name: 'Scallops', description: 'Sweet sea scallops' },
          { name: 'Salmon', description: 'Fresh Atlantic salmon' },
          { name: 'Lobster Tail', description: 'Premium lobster tail' },
        ],
      },
      {
        name: 'Specialty',
        items: [
          { name: 'Tofu', description: 'Firm, seasoned tofu' },
          { name: 'Vegetables', description: 'Mixed seasonal vegetables' },
        ],
      },
    ],
  },

  serviceAreas: {
    title: '🌟 Bringing Hibachi Experience to Your Neighborhood! 🌟',
    subtitle:
      "We bring the hibachi experience to homes and venues across the Bay Area, Sacramento, San Jose and nearby communities. Need us a bit farther? Tell us your location—we'll make it work with transparent travel options.",
    primary: {
      title: '🏙️ Primary Bay Area Locations',
      subtitle: 'No additional travel fees within these areas!',
      locations: [
        'San Francisco - The heart of culinary excellence',
        "San Jose - Silicon Valley's finest hibachi",
        'Oakland - East Bay entertainment at its best',
        'Bay Area - Our home base with premium service',
        'Santa Clara - Tech meets traditional Japanese cuisine',
        'Sunnyvale - Where innovation meets flavor',
        'Mountain View - Bringing mountains of flavor',
        'Palo Alto - Stanford-level culinary performance',
      ],
    },
    extended: {
      title: '🚗 Extended Service Areas',
      subtitle: 'We travel farther for unforgettable experiences!',
      locations: [
        'Sacramento - Capital city hibachi excellence',
        "Modesto - Central Valley's hibachi destination",
        'Stockton - Bringing flavor to the Central Valley',
        "Fresno - Central California's hibachi experience",
        'San Mateo - Peninsula dining excellence',
        'Fremont - South Bay hibachi artistry',
      ],
    },
  },

  additionalServices: {
    title: 'Enhance Your Experience',
    subtitle: 'Optional add-ons to make your event even more special',
    items: [
      {
        name: 'Premium Sake Service',
        price: '$25',
        description: 'Traditional sake service with premium selection',
      },
      {
        name: 'Extended Performance',
        price: '$50',
        description: 'Additional 30 minutes of entertainment and tricks',
      },
      {
        name: 'Custom Menu Planning',
        price: '$35',
        description: 'Personalized menu consultation and planning',
      },
    ],
  },
};

export type MenuData = typeof menuData;
