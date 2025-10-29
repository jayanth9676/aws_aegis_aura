# Aegis Frontend - Modern Fraud Prevention Interface

A beautiful, production-ready Next.js frontend for the Aegis Fraud Prevention Platform.

## 🎨 Features

### For Analysts
- **Real-time Dashboard**: Live metrics, high-risk case alerts, performance KPIs
- **Advanced Case Management**: Powerful filters, sorting, search with pagination
- **Comprehensive Case Details**: Risk assessment, evidence timeline, agent reasoning, network graphs, SHAP explainability
- **AI Co-pilot**: Intelligent assistant powered by Claude Sonnet 4 for fraud analysis
- **Analytics Dashboard**: Charts for fraud trends, risk distribution, typology breakdown, model metrics
- **Real-time Updates**: WebSocket integration for instant case updates and notifications

### For Customers
- **Security Dashboard**: Transaction monitoring with AI protection status
- **Interactive Verification**: Conversational AI for transaction verification
- **Fraud Education**: Comprehensive scam prevention tips and resources
- **Security Alerts**: High-visibility warnings for suspicious transactions

### Design & UX
- **Modern UI**: Built with shadcn/ui and Tailwind CSS
- **Responsive**: Mobile-first design that works on all devices
- **Accessible**: WCAG compliant with keyboard navigation
- **Fast**: Optimized with React Query for data fetching and caching
- **Professional**: Financial services color palette and typography

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js 14 App Router
│   ├── analyst/           # Analyst-facing pages
│   │   ├── page.tsx       # Dashboard
│   │   ├── cases/         # Case management
│   │   ├── copilot/       # AI co-pilot
│   │   └── dashboard/     # Analytics
│   ├── customer/          # Customer-facing pages
│   │   ├── page.tsx       # Customer dashboard
│   │   └── dialogue/      # Fraud verification
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/
│   ├── analyst/           # Analyst components
│   │   ├── case-details/  # Case detail views
│   │   ├── copilot/       # Co-pilot interface
│   │   └── analytics/     # Charts and metrics
│   ├── customer/          # Customer components
│   ├── layout/            # Layout components
│   ├── shared/            # Shared components
│   └── visualizations/    # D3.js charts
├── hooks/                 # Custom React hooks
│   ├── useWebSocket.ts    # WebSocket management
│   └── useCaseUpdates.ts  # Real-time case updates
├── lib/
│   ├── api-client.ts      # API client with retry logic
│   └── utils.ts           # Utility functions
└── types/
    └── index.ts           # TypeScript definitions
```

## 🎯 Key Pages

### Analyst Portal
- `/analyst` - Main dashboard with stats and activity feed
- `/analyst/cases` - Case list with advanced filtering
- `/analyst/cases/[id]` - Detailed case view with all evidence
- `/analyst/copilot` - AI assistant for fraud analysis
- `/analyst/dashboard` - Analytics with charts and metrics

### Customer Portal
- `/customer` - Customer dashboard with recent transactions
- `/customer/dialogue/[transaction_id]` - Interactive fraud verification

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI)
- **Charts**: Recharts, D3.js
- **Data Fetching**: TanStack Query (React Query)
- **Real-time**: WebSocket
- **Notifications**: React Hot Toast
- **Icons**: Lucide React
- **Date**: date-fns

## 🎨 Component Library

All components are built with shadcn/ui:

```bash
# Add new components
npx shadcn@latest add [component-name]
```

Available components:
- Button, Card, Badge, Alert
- Table, Tabs, Dialog, Dropdown
- Form inputs (Input, Textarea, Select, Checkbox)
- Accordion, ScrollArea, Skeleton
- And more...

## 📡 API Integration

The frontend communicates with the backend via:

### REST API
```typescript
import { apiClient } from '@/lib/api-client'

// Get cases
const cases = await apiClient.getCases({ 
  filters: { status: ['NEW'] }
})

// Get case details
const case = await apiClient.getCase('CASE-1234')

// Perform case action
await apiClient.caseAction('CASE-1234', {
  action: 'BLOCK',
  reason: 'High fraud risk'
})
```

### WebSocket
```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const { isConnected, sendMessage } = useWebSocket({
  onMessage: (message) => {
    console.log('Received:', message)
  }
})
```

## 🔍 Type Safety

Full TypeScript coverage with comprehensive interfaces:

```typescript
import type { Case, Transaction, AgentMessage } from '@/types'
```

## 🎭 Theming

Customizable theme with CSS variables in `globals.css`:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;
  /* ... */
}
```

## ⚡ Performance

- **Code Splitting**: Automatic route-based code splitting
- **Image Optimization**: Next.js Image component
- **Caching**: React Query with smart invalidation
- **Bundle Analysis**: `npm run build` shows bundle sizes

## 🧪 Testing

```bash
# Run E2E tests with Playwright
npm run test:e2e

# Run tests in UI mode
npm run test:e2e:ui

# View test report
npm run test:e2e:report
```

## 📱 Mobile Optimization

- Responsive layouts for all screen sizes
- Touch-optimized controls
- Mobile-friendly navigation (hamburger menu)
- Optimized charts for small screens

## ♿ Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation support
- Screen reader friendly
- Focus management
- ARIA labels and roles

## 🚢 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker
```bash
# Build
docker build -t aegis-frontend .

# Run
docker run -p 3000:3000 aegis-frontend
```

### AWS Amplify
```bash
amplify init
amplify add hosting
amplify publish
```

## 📊 Monitoring

Integrate with monitoring services:
- **Analytics**: Vercel Analytics, Google Analytics
- **Error Tracking**: Sentry
- **Performance**: Vercel Speed Insights

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for all new files
3. Follow Tailwind CSS conventions
4. Add proper ARIA labels for accessibility
5. Test on mobile devices

## 📄 License

Private - Aegis Fraud Prevention Platform

## 🆘 Support

For issues or questions:
- Check backend API is running on http://localhost:8000
- Verify environment variables are set
- Check browser console for errors
- Review Network tab for failed API calls

## 🎉 Features Implemented

✅ Complete analyst dashboard with real-time updates
✅ Advanced case management system
✅ Comprehensive case details with visualizations
✅ AI co-pilot chat interface
✅ Analytics dashboard with charts
✅ Customer portal with fraud verification
✅ WebSocket real-time updates
✅ Full TypeScript coverage
✅ Mobile responsive design
✅ Accessibility features
✅ Production-ready components

**Status**: ✨ Production Ready!

