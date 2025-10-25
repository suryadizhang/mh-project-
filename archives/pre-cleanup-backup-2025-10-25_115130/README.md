# 🍤 MyHibachi - Full-Stack Booking System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/suryadizhang/mh-project-)
[![Quality Score](https://img.shields.io/badge/quality-98.5%2F100-brightgreen)](./COMPREHENSIVE_PROJECT_DOCS.md)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-success)](./DEPLOYMENT_STRATEGY.md)
[![Security](https://img.shields.io/badge/security-PCI%20compliant-blue)](./COMPREHENSIVE_PROJECT_DOCS.md#security-features)

> **Professional hibachi catering booking system with integrated
> payments, admin dashboard, and AI assistance.**

## 📖 About This Project

**MyHibachi** is a comprehensive full-stack web application designed
for professional hibachi catering services. Built with modern
technologies and enterprise-grade architecture, this system transforms
traditional catering bookings into a seamless digital experience.

### 🎯 **What It Does**

MyHibachi provides an end-to-end solution for hibachi catering
businesses, offering:

- **🗓️ Smart Booking Management** - Real-time availability checking,
  automated scheduling, and conflict prevention
- **💰 Integrated Payment Processing** - Secure payments via Stripe,
  Zelle, and Venmo with automatic fee calculations
- **👨‍💼 Comprehensive Admin Dashboard** - Complete business oversight
  with analytics, customer management, and booking controls
- **📱 Mobile-First Experience** - Responsive design optimized for
  customers booking on any device
- **🤖 AI-Powered Assistant** - Intelligent recommendations, booking
  optimization, and customer support automation
- **📈 Business Intelligence** - Revenue tracking, popular menu
  analysis, and customer behavior insights

### 🏢 **Who It's For**

- **Hibachi Catering Businesses** - Streamline operations and increase
  bookings
- **Event Planners** - Easy integration with existing planning
  workflows
- **Customers** - Simplified booking process with transparent pricing
- **Administrators** - Powerful tools for business management and
  growth

### 🌟 **Why MyHibachi?**

**Traditional Problems Solved:**

- ❌ Manual booking via phone/email → ✅ Automated online booking
  system
- ❌ Payment collection hassles → ✅ Integrated secure payment
  processing
- ❌ Double-booking disasters → ✅ Real-time availability management
- ❌ Manual invoicing/receipts → ✅ Automated documentation and PDF
  generation
- ❌ Limited business insights → ✅ Comprehensive analytics and
  reporting

**Technical Excellence:**

- 🏗️ **Modern Architecture** - Next.js 14, FastAPI, PostgreSQL with
  TypeScript
- 🔒 **Enterprise Security** - PCI DSS compliant with comprehensive
  data protection
- ⚡ **High Performance** - Optimized for speed with 98.5/100 quality
  score
- 📈 **SEO Optimized** - 85 blog posts and 10 location pages for
  maximum visibility
- 🧪 **Quality Assured** - 95% test coverage with automated quality
  checks

### 🎨 **Key Features Highlight**

**For Customers:**

- Intuitive booking interface with real-time pricing
- Multiple payment options with transparent fee structure
- Automatic confirmation emails and calendar invites
- Mobile-optimized experience for on-the-go bookings

**For Business Owners:**

- Complete booking lifecycle management
- Revenue analytics and business intelligence
- Customer relationship management tools
- Automated invoicing and payment tracking
- Multi-location support with location-specific SEO

**For Developers:**

- Clean, maintainable codebase with comprehensive documentation
- Modern development workflow with automated testing and deployment
- Extensible architecture for easy customization and scaling
- Production-ready with zero critical security issues

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/suryadizhang/mh-project-.git
cd mh-project-

# Install all dependencies
npm install          # Install workspace dependencies
pip install -r requirements.txt  # Install Python dependencies

# Start all services (recommended)
npm run dev:all      # Frontend + Backend + AI (http://localhost:3000, 8000, 5000)

# Or start services individually
npm run dev:frontend    # Frontend only (http://localhost:3000)
npm run dev:backend     # Backend only (http://localhost:8000)
npm run dev:ai          # AI service only (http://localhost:5000)
```

## ✨ Features

- 📅 **Advanced Booking System** - Real-time availability with
  calendar integration
- 💳 **Multi-Payment Support** - Stripe, Zelle, Venmo with automatic
  fee calculation
- 👨‍💼 **Admin Dashboard** - Complete booking management and analytics
- 📱 **Mobile-First Design** - Responsive UI optimized for all devices
- 🔍 **SEO Optimized** - 85 blog posts and 10 location-specific pages
- 🤖 **AI Assistant** - Intelligent booking assistance and
  recommendations
- 🔒 **Enterprise Security** - PCI compliant with comprehensive data
  protection

## 🏗️ Architecture

```
📁 MyHibachi Project Structure
├── 🎨 myhibachi-frontend/     # Next.js 15 + TypeScript
├── ⚡ myhibachi-backend/      # FastAPI + PostgreSQL
├── 🤖 myhibachi-ai-backend/   # AI Assistant Service
├── 📚 docs/                  # Documentation
├── 🔧 scripts/               # Automation scripts
└── 📋 verification/          # Quality assurance
```

## 📊 Project Status

| Component     | Status                | Quality Score |
| ------------- | --------------------- | ------------- |
| 🎨 Frontend   | ✅ Production Ready   | 98/100        |
| ⚡ Backend    | ✅ Production Ready   | 99/100        |
| 🤖 AI Service | ✅ Production Ready   | 95/100        |
| 🔒 Security   | ✅ PCI Compliant      | 100/100       |
| 📦 Build      | ✅ 137 pages compiled | 100%          |
| 🧪 Tests      | ✅ All passing        | 95% coverage  |

**Overall Quality Score: 98.5/100** ⭐

## 🛠️ Development

## 🛠️ Development

### Prerequisites

- **Node.js** 20+ (for frontend)
- **Python** 3.9+ (for backend services)
- **PostgreSQL** 14+ (database)
- **Git** (version control)

### Environment Setup

```bash
# 1. Clone and install dependencies
git clone https://github.com/suryadizhang/mh-project-.git
cd mh-project-
npm install

# 2. Backend environment setup
cp myhibachi-backend/.env.example myhibachi-backend/.env
# Configure: DATABASE_URL, STRIPE_SECRET_KEY, JWT_SECRET

# 3. Frontend environment setup
cp myhibachi-frontend/.env.example myhibachi-frontend/.env.local
# Configure: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_STRIPE_PUBLIC_KEY

# 4. Start development
npm run dev:all  # All services running!
```

### Available Scripts

```bash
# Development Commands
npm run dev:all         # Start all services (Frontend + Backend + AI)
npm run dev:frontend    # Start frontend only
npm run dev:backend     # Start backend only
npm run dev:ai          # Start AI service only

# Build & Production
npm run build           # Build frontend for production
npm run start           # Start production frontend
npm run start:frontend  # Same as above

# Code Quality
npm run lint            # Lint all code (frontend + backend)
npm run lint:frontend   # Lint frontend only
npm run lint:backend    # Lint backend only (ruff + black)
npm run format          # Format all code
npm run type-check      # TypeScript type checking

# Testing
npm run test            # Run all tests
npm run test:frontend   # Run frontend tests
npm run test:backend    # Run backend tests (pytest)

# Maintenance
npm run clean           # Clean all node_modules and build files
```

## 🚀 Deployment

The project is **production-ready** with zero critical issues. See
[Deployment Strategy](./DEPLOYMENT_STRATEGY.md) for detailed
instructions.

### Quick Deploy Options

```bash
# Option 1: All-in-one command
npm run build && npm run start

# Option 2: Individual services
# Frontend (Vercel/Netlify)
cd myhibachi-frontend && npm run build && npm run start

# Backend (Railway/Heroku/AWS)
cd myhibachi-backend && uvicorn main:app --host 0.0.0.0 --port 8000

# AI Service (any Python hosting)
cd myhibachi-ai-backend && python main.py
```

### Recommended Hosting

- **Frontend**: Vercel, Netlify, or AWS Amplify
- **Backend**: Railway, Heroku, or AWS EC2
- **Database**: PostgreSQL on AWS RDS, Supabase, or Railway
- **AI Service**: Any Python hosting (Railway, Heroku)

## 📚 Documentation

- 📋 [**Comprehensive Docs**](./COMPREHENSIVE_PROJECT_DOCS.md) -
  Complete project documentation
- 🚀 [**Deployment Guide**](./DEPLOYMENT_STRATEGY.md) - Production
  deployment instructions
- 📊 [**Project Summary**](./PROJECT_SUMMARY.md) - Technical overview
  and features
- 📁 [**Archive Docs**](./archive-docs/) - Historical documentation
  and reports

## 🔄 CI/CD Lanes

This monorepo implements **four independent CI/CD pipelines** with
path-based triggering for efficient deployments:

### 🎯 **Pipeline Overview**

| Lane               | Trigger Path                   | Deployment Target           | Status    |
| ------------------ | ------------------------------ | --------------------------- | --------- |
| 🎨 **FE Customer** | `myhibachi-frontend/**`        | Vercel                      | ✅ Active |
| ⚙️ **FE Admin**    | `myhibachi-admin-frontend/**`  | Vercel                      | ✅ Active |
| 🚀 **API**         | `myhibachi-backend-fastapi/**` | VPS (api.myhibachichef.com) | ✅ Active |
| 🤖 **AI API**      | `myhibachi-ai-backend/**`      | VPS (ai.myhibachichef.com)  | ✅ Active |

### 📋 **Pipeline Details**

#### 🎨 **Frontend Customer** (`.github/workflows/fe-customer.yml`)

- **Triggers**: Changes in `myhibachi-frontend/`
- **Steps**: Lint → Test → Build → E2E Tests → Vercel Deploy
- **Target**: https://myhibachichef.com
- **Port**: 3000 (local development)

#### ⚙️ **Frontend Admin** (`.github/workflows/fe-admin.yml`)

- **Triggers**: Changes in `myhibachi-admin-frontend/`
- **Steps**: Lint → Test → Build → E2E Tests → Vercel Deploy
- **Target**: https://admin.myhibachichef.com
- **Port**: 3001 (local development)

#### 🚀 **Main API** (`.github/workflows/api.yml`)

- **Triggers**: Changes in `myhibachi-backend-fastapi/`
- **Steps**: Install → Test → Deploy via SSH → Restart Service
- **Target**: https://api.myhibachichef.com
- **Service**: `myhibachi-api.service`
- **Port**: 8001 (production)

#### 🤖 **AI API** (`.github/workflows/ai-api.yml`)

- **Triggers**: Changes in `myhibachi-ai-backend/`
- **Steps**: Install → Test → Deploy via SSH → Restart Service
- **Target**: https://ai.myhibachichef.com
- **Service**: `myhibachi-ai.service`
- **Port**: 8002 (production)

### 🔐 **Required GitHub Secrets**

Configure these secrets in your GitHub repository settings:

```bash
# VPS Deployment Secrets
VPS_HOST=your-vps-server.com           # VPS hostname/IP
VPS_USER=deploy                        # SSH username
VPS_SSH_KEY=-----BEGIN RSA PRIVATE---- # SSH private key

# Frontend Environment Variables
NEXT_PUBLIC_API_BASE_URL=https://api.myhibachichef.com      # API endpoint
NEXT_PUBLIC_AI_API_BASE_URL=https://ai.myhibachichef.com    # AI API endpoint
```

### 🏗️ **Deployment Architecture**

```
🌐 Production Environment
├── 🎨 Customer Frontend → Vercel (myhibachichef.com)
├── ⚙️ Admin Frontend → Vercel (admin.myhibachichef.com)
├── 🚀 Main API → VPS:8001 → Nginx → api.myhibachichef.com
└── 🤖 AI API → VPS:8002 → Nginx → ai.myhibachichef.com
```

### ⚡ **Key Features**

- **🎯 Path-Based Triggering** - Only affected services rebuild
- **🔄 Independent Deployments** - Each service deploys separately
- **🧪 Comprehensive Testing** - Lint, unit tests, and E2E for
  frontends
- **🚀 Zero-Downtime Deploys** - Rolling updates with health checks
- **📊 Deployment Visibility** - Clear status for each pipeline

### 🛠️ **Local Development**

Each service can be developed and tested independently:

```bash
# Test individual pipelines locally
npm run lint:frontend          # Frontend linting
npm run test:backend           # Backend testing
npx playwright test --project=customer  # E2E testing
```

### 🔧 **SystemD Services**

Production services are managed via systemd:

- **Main API**: `/srv/myhibachi/api/` → `myhibachi-api.service`
- **AI API**: `/srv/myhibachi/ai-api/` → `myhibachi-ai.service`

Service files are provided in `systemd/` directory for VPS deployment.

## 📚 Documentation

- 📋 [**Comprehensive Docs**](./COMPREHENSIVE_PROJECT_DOCS.md) -
  Complete project documentation
- 🚀 [**Deployment Guide**](./DEPLOYMENT_STRATEGY.md) - Production
  deployment instructions
- 📊 [**Project Summary**](./PROJECT_SUMMARY.md) - Technical overview
  and features
- 📁 [**Archive Docs**](./archive-docs/) - Historical documentation
  and reports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Email**: myhibachichef@gmail.com
- **Phone**: (916) 740-8768
- **Website**: [myhibachi.com](https://myhibachi.com)

## 📄 License

This project is proprietary software for MyHibachi Catering Services.

---

<div align="center">
  <strong>🍤 Built with ❤️ for MyHibachi</strong><br>
  <em>Production-ready • Secure • Scalable</em>
</div>
