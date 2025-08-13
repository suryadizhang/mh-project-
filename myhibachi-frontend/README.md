# MyHibachi Frontend

A modern, responsive website for MyHibachi catering business built with Next.js, TypeScript, Tailwind CSS, and shadcn/ui.

## Features

- **Modern Design**: Clean, responsive design with Tailwind CSS
- **Complete Site Structure**: Home, Menu, Contact, Reviews, FAQs, and Blog pages
- **Admin Dashboard**: Full-featured admin panel with booking management, scheduling, newsletter, logs, customer management, and super admin controls
- **Page-Specific Styling**: Preserves original CSS while modernizing the UI
- **Component Architecture**: Reusable components with shadcn/ui integration

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Custom CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── admin/             # Admin dashboard with layout
│   │   ├── booking/       # Booking management
│   │   ├── schedule/      # Chef scheduling
│   │   ├── newsletter/    # Newsletter management
│   │   ├── logs/          # System logs
│   │   ├── customers/     # Customer management
│   │   └── superadmin/    # System administration
│   ├── blog/              # Blog page
│   ├── contact/           # Contact page
│   ├── faqs/              # FAQ page
│   ├── menu/              # Menu page
│   ├── review/            # Reviews page
│   └── layout.tsx         # Root layout with navbar/footer
├── components/
│   ├── layout/            # Layout components
│   │   ├── Navbar.tsx     # Main navigation
│   │   ├── Footer.tsx     # Site footer
│   │   └── AdminSidebar.tsx # Admin sidebar
│   └── ui/                # shadcn/ui components
└── styles/                # Page-specific CSS
    ├── home.css
    ├── menu.css
    └── contact.css
```

## Getting Started

1. **Install dependencies**:
```bash
npm install
```

2. **Run the development server**:
```bash
npm run dev
```

3. **Open your browser**:
Navigate to [http://localhost:3000](http://localhost:3000)

## Pages

### Public Pages
- **Home** (`/`) - Hero section, features, stats, and CTA
- **Menu** (`/menu`) - Hibachi menu with categories and pricing
- **Contact** (`/contact`) - Contact form and business information
- **Reviews** (`/review`) - Customer testimonials
- **FAQs** (`/faqs`) - Frequently asked questions
- **Blog** (`/blog`) - Blog posts and articles

### Admin Pages
- **Dashboard** (`/admin`) - Overview and statistics
- **Bookings** (`/admin/booking`) - Manage reservations
- **Schedule** (`/admin/schedule`) - Chef scheduling and calendar
- **Newsletter** (`/admin/newsletter`) - Email campaigns and subscribers
- **Logs** (`/admin/logs`) - System activity logs
- **Customers** (`/admin/customers`) - Customer database
- **Super Admin** (`/admin/superadmin`) - System administration

## Development

### Adding New Pages
1. Create a new directory in `src/app/`
2. Add a `page.tsx` file
3. Import any page-specific CSS if needed

### Adding Components
1. Add components to `src/components/`
2. Use shadcn/ui components when possible
3. Follow TypeScript best practices

### Styling
- Use Tailwind CSS for layout and common styles
- Create page-specific CSS files in `src/styles/` for unique styling
- Import CSS files directly in page components

## Build and Deploy

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Live Chat Support

This project includes tawk.to live chat integration for customer support:

### For Operators
- Install the tawk.to app on iOS/Android
- Sign in with the property credentials
- Enable push notifications to reply on the go
- Chat widget automatically appears on all pages except admin routes

### Configuration
Live chat is configured via environment variables in `.env.local`:
- `NEXT_PUBLIC_TAWK_PROPERTY_ID`: Your tawk.to property ID
- `NEXT_PUBLIC_TAWK_WIDGET_ID`: Widget ID (defaults to "default")

### Features
- Automatic loading on all public pages
- Hidden on admin routes (/admin, /superadmin, /checkout)
- Custom "Live Chat" buttons on contact page
- Visitor attribute setting capability
- TypeScript support

## License

Private project for MyHibachi catering business.
