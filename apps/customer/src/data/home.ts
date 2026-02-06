export const homeData = {
  hero: {
    videoSrc: '/videos/hero_video.mp4',
    title: 'Experience the Art of Japanese Hibachi',
    subtitle: 'Where Culinary Mastery Meets Unforgettable Entertainment',
    qualityBadge:
      '🌟 Premium Quality Ingredients • Reasonable Prices • Excellence is Our Priority 🌟',
  },

  experience: {
    chef: {
      title: '🧑‍🍳 Meet Your Private Chef',
      content:
        'Our skilled hibachi chefs bring years of training in traditional Japanese cooking techniques. From precise knife work to spectacular flame displays, every movement is choreographed to deliver both incredible food and unforgettable entertainment.',
    },
    entertainment: {
      title: '🎭 Interactive Entertainment',
      content:
        "More than just a meal - it's a show! Watch in amazement as your chef performs tricks with utensils, creates towering onion volcanoes, and engages your guests with humor and skill. Perfect for celebrations, date nights, or family gatherings.",
    },
  },

  features: [
    {
      icon: '👨‍🍳',
      title: 'Professional Chefs',
      description:
        'Trained in traditional Japanese hibachi techniques with years of experience in both cooking and entertainment.',
    },
    {
      icon: '🏠',
      title: 'We Come to You',
      description:
        'No need to travel! We bring the complete hibachi experience directly to your home, backyard, or venue.',
    },
    {
      icon: '🍱',
      title: 'Fresh Ingredients',
      description:
        'Premium quality meats, seafood, and vegetables. All ingredients are fresh, never frozen, and sourced locally when possible.',
    },
    {
      icon: '🎯',
      title: 'Customizable Menu',
      description:
        'Choose from chicken, steak, shrimp, scallops, salmon, and more. We accommodate dietary restrictions and preferences.',
    },
    {
      icon: '🧽',
      title: 'Full Setup & Cleanup',
      description:
        'We handle everything - equipment setup, cooking, serving, and complete cleanup. You just enjoy the experience!',
    },
    {
      icon: '💎',
      title: 'Premium Experience',
      description:
        'Authentic hibachi dining with professional-grade equipment and restaurant-quality presentation in your own space.',
    },
  ],

  serviceAreas: {
    title: '🌟 Bringing Hibachi Experience to Your Neighborhood! 🌟',
    subtitle:
      "We bring the hibachi experience to homes and venues across the Bay Area, Sacramento, San Jose and nearby communities. Need us a bit farther? Tell us your location—we'll make it work with transparent travel options.",
    ctaButtons: [
      {
        href: '/book-us/',
        text: '📅 Check Your Date & Time',
        primary: true,
      },
      {
        href: '/quote',
        text: '💬 Get a Quick Quote',
        primary: false,
      },
    ],
    areas: {
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
  },

  cta: {
    title: 'Ready to Transform Your Next Event?',
    subtitle: 'Book your unforgettable hibachi experience today!',
    buttons: [
      {
        href: '/book-us/',
        text: '📅 Book Your Event',
        primary: true,
      },
      {
        href: '/menu',
        text: '🍱 View Full Menu',
        primary: false,
      },
    ],
  },

  about: {
    title: 'Why Choose My Hibachi?',
    description:
      "We're passionate about bringing authentic Japanese hibachi dining to your doorstep. With professional chefs, premium ingredients, and full-service setup, we create memorable experiences that bring people together over incredible food and entertainment.",
  },

  services: {
    title: 'Our Services',
    items: [
      {
        icon: '🎂',
        title: 'Birthday Parties',
        description: 'Make birthdays unforgettable with hibachi entertainment',
      },
      {
        icon: '💑',
        title: 'Date Nights',
        description: 'Romantic hibachi dinners in the comfort of your home',
      },
      {
        icon: '👨‍👩‍👧‍👦',
        title: 'Family Gatherings',
        description: 'Bring the family together with interactive dining',
      },
      {
        icon: '🏢',
        title: 'Corporate Events',
        description: 'Team building and client entertainment that impresses',
      },
      {
        icon: '🎉',
        title: 'Special Celebrations',
        description: 'Anniversaries, graduations, and milestone events',
      },
      {
        icon: '🏠',
        title: 'Private Parties',
        description: 'Intimate gatherings with personalized service',
      },
    ],
  },
};

export type HomeData = typeof homeData;
