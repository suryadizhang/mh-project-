const fs = require('fs');
const path = require('path');

const CONTENT_DIR = path.join(__dirname, 'apps', 'customer', 'content', 'blog', 'posts');

function generateContent(frontmatter) {
  // Extract metadata from frontmatter
  const titleMatch = frontmatter.match(/title:\s*["'](.+?)["']/);
  const serviceAreaMatch = frontmatter.match(/serviceArea:\s*["'](.+?)["']/);
  const eventTypeMatch = frontmatter.match(/eventType:\s*["'](.+?)["']/);
  const excerptMatch = frontmatter.match(/excerpt:\s*["'](.+?)["']/);
  const categoryMatch = frontmatter.match(/category:\s*["'](.+?)["']/);

  const title = titleMatch ? titleMatch[1] : 'Hibachi Catering Event';
  const serviceArea = serviceAreaMatch ? serviceAreaMatch[1] : 'Bay Area';
  const eventType = eventTypeMatch ? eventTypeMatch[1] : 'Event';
  const excerpt = excerptMatch ? excerptMatch[1] : '';
  const category = categoryMatch ? categoryMatch[1] : 'Events';

  return `
## ${title}

${excerpt}

### Transform Your ${eventType} with Professional Hibachi Catering

Experience the magic of hibachi cooking at your ${eventType.toLowerCase()} in ${serviceArea}! My Hibachi brings authentic Japanese hibachi entertainment and cuisine directly to your venue, creating an unforgettable culinary experience that your guests will rave about.

### Why Choose My Hibachi for Your ${eventType}?

#### 🔥 **Expert Hibachi Chefs**
Our professionally trained chefs don't just cook—they perform! With years of experience in authentic Japanese hibachi techniques, they transform meal preparation into an exciting show complete with:
- Dazzling knife work and tricks
- Interactive cooking demonstrations
- Personalized attention to guests
- Professional showmanship that entertains all ages

#### 🥩 **Premium Quality Ingredients**
We never compromise on quality. Every dish features:
- **USDA Choice or Higher Meats**: Perfectly marbled steaks and tender chicken
- **Fresh Seafood**: Succulent shrimp and premium fish
- **Crisp Vegetables**: Locally-sourced when available
- **Authentic Seasonings**: Traditional Japanese flavors
- **Dietary Accommodations**: Vegetarian, vegan, and allergen-friendly options

#### 🎪 **Complete Event Service**
From setup to cleanup, we handle everything:
- Professional-grade hibachi grills delivered to your location
- All cooking equipment, utensils, and serving ware
- Fresh ingredients prepared on-site
- Full setup before your event
- Complete cleanup after service
- Flexible scheduling to fit your timeline

### Perfect for ${serviceArea} ${category}

Whether you're hosting in ${serviceArea} or surrounding communities, we bring the same level of excellence to every event. Our mobile hibachi catering is ideal for:

- **Private Parties**: Birthdays, anniversaries, and celebrations
- **Corporate Events**: Team building, client entertainment, holiday parties
- **Weddings**: Rehearsal dinners and reception alternatives
- **Family Gatherings**: Reunions, graduations, and milestones
- **Outdoor Events**: Backyard parties, pool parties, and garden celebrations
- **Special Occasions**: Any event that deserves extraordinary catering

### What Makes Us Different

#### Local ${serviceArea} Expertise
We understand the unique needs of ${serviceArea} events:
- Familiar with local venues and regulations
- Knowledge of ${serviceArea} neighborhoods and access requirements
- Experienced with ${serviceArea} weather and outdoor setups
- Strong relationships with local suppliers

#### Customizable Menu Options
Choose from our extensive menu or create a custom experience:
- **Signature Proteins**: Filet mignon, ribeye, chicken, shrimp, salmon, lobster
- **Vegetable Medley**: Zucchini, onions, mushrooms, broccoli, and more
- **Fried Rice**: Classic or vegetable fried rice
- **Noodles**: Lo mein or udon options
- **Appetizers**: Edamame, gyoza, salad
- **Sauces**: Ginger, yum yum, teriyaki, and more

#### Stress-Free Experience
We handle all the details so you can enjoy your event:
1. **Easy Booking**: Simple quote process and flexible scheduling
2. **Professional Setup**: We arrive early to set up completely
3. **Entertainment Included**: Cooking show amazes your guests
4. **Fresh Cooking**: Everything prepared fresh on-site
5. **Complete Cleanup**: We leave your space spotless

### How It Works

#### 1. **Get Your Free Quote**
Contact us with your event details:
- Date and time
- Number of guests
- Location in ${serviceArea}
- Menu preferences

#### 2. **Customize Your Menu**
Work with our team to create the perfect menu for your ${eventType.toLowerCase()}. We accommodate all dietary needs and preferences.

#### 3. **Confirm & Relax**
Once booked, we handle everything. Just provide the space, and we'll bring the experience!

#### 4. **Enjoy the Show**
Watch as our expert chefs entertain and delight your guests with fresh, delicious hibachi cuisine.

### Serving ${serviceArea} and Beyond

My Hibachi proudly serves ${serviceArea} and surrounding communities. Our mobile setup allows us to bring premium hibachi catering to:
- Residential homes and backyards
- Community centers and clubhouses
- Corporate offices and event spaces
- Parks and outdoor venues
- Any location you choose!

### Customer Testimonials

*"The hibachi chef made our ${eventType.toLowerCase()} absolutely incredible! Our guests are still talking about it weeks later. The food was delicious and the entertainment was top-notch."*

*"We've used My Hibachi for multiple events now. Every time, they exceed our expectations. Professional, entertaining, and the food is always amazing."*

*"Best catering decision we ever made! The interactive cooking show kept everyone engaged, and the quality of the food was restaurant-level. Highly recommend for any ${serviceArea} event!"*

### Book Your ${eventType} Today

Ready to elevate your ${eventType.toLowerCase()} in ${serviceArea}? My Hibachi makes it easy to create an extraordinary culinary experience your guests will never forget.

#### Contact Us
**Phone**: (916) 740-8768  
**Email**: info@myhibachi.com  
**Service Area**: ${serviceArea} and surrounding communities

#### Get Started
1. Call or email for a free quote
2. Discuss your menu preferences
3. Confirm your booking
4. Enjoy your unforgettable hibachi experience!

### Frequently Asked Questions

**Q: How much space do you need?**  
A: We need approximately 10x10 feet for our grill setup, plus clear access to the cooking area.

**Q: Do you provide tables and chairs?**  
A: We focus on the cooking experience. Tables, chairs, and dining setup are typically provided by the host or venue.

**Q: How long does the cooking take?**  
A: For most events, we cook in batches of 8-10 guests at a time, with each batch taking about 20-30 minutes.

**Q: Can you accommodate dietary restrictions?**  
A: Absolutely! We offer vegetarian, vegan, gluten-free, and allergen-friendly options.

**Q: What if the weather is bad?**  
A: We can set up in covered outdoor areas or garages. For safety, we require some ventilation and weather protection for our grills.

### Why Hibachi Catering is Perfect for Your ${eventType}

Hibachi catering offers unique advantages over traditional catering:
- **Interactive Entertainment**: Guests are engaged and entertained
- **Fresh Cooking**: No reheated food—everything cooked to order
- **Customizable**: Each guest can request their preferences
- **Memorable**: Creates lasting memories and conversation
- **Social**: Brings guests together around the grill
- **Photo-Worthy**: Amazing visuals for social media

### Make Your ${eventType} Unforgettable

Don't settle for ordinary catering when you can have an extraordinary experience! My Hibachi combines world-class cuisine with exciting entertainment, creating the perfect centerpiece for your ${eventType.toLowerCase()} in ${serviceArea}.

**Call (916) 740-8768 today** to discuss your event and receive a free, no-obligation quote. Let's make your ${eventType.toLowerCase()} truly unforgettable!

---

*My Hibachi - Bringing Premium Hibachi Entertainment to ${serviceArea} Since 2020*
`;
}

function processDirectory(dir) {
  if (!fs.existsSync(dir)) {
    console.error(`Directory not found: ${dir}`);
    return 0;
  }

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let updated = 0;

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      updated += processDirectory(fullPath);
    } else if (entry.name.endsWith('.mdx') || entry.name.endsWith('.md')) {
      try {
        const content = fs.readFileSync(fullPath, 'utf8');

        if (content.includes('No content available')) {
          const parts = content.split('---');
          if (parts.length >= 3) {
            const frontmatter = parts[1];
            const newContent = `---${frontmatter}---\n${generateContent(frontmatter)}\n`;

            fs.writeFileSync(fullPath, newContent, 'utf8');
            console.log(`✓ Updated: ${entry.name}`);
            updated++;
          }
        } else {
          console.log(`⊘ Skipped (has content): ${entry.name}`);
        }
      } catch (error) {
        console.error(`✗ Error processing ${entry.name}:`, error.message);
      }
    }
  }

  return updated;
}

console.log('🚀 Starting blog content update...\n');
console.log(`📂 Content directory: ${CONTENT_DIR}\n`);

const total = processDirectory(CONTENT_DIR);

console.log(`\n${'='.repeat(50)}`);
console.log(`✅ Updated ${total} blog posts!`);
console.log(`${'='.repeat(50)}\n`);

if (total > 0) {
  console.log('📝 Next steps:');
  console.log('  1. Start dev server: npm run dev');
  console.log('  2. Visit: http://localhost:3000/blog');
  console.log('  3. Verify content appears correctly');
  console.log('  4. Customize top posts with detailed content');
  console.log('  5. Add relevant images to posts\n');
} else {
  console.log('ℹ️  No files needed updating (all posts already have content)\n');
}
