# AI Job Hunting Assistant - Frontend

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── dashboard/       # Dashboard tab components
│   │   └── interview/       # Interview tab components
│   ├── pages/               # Main page components
│   │   ├── InputPage.tsx    # Input page (JD, Resume, Projects)
│   │   ├── LoadingPage.tsx  # Loading page with progress
│   │   ├── DashboardPage.tsx # Main dashboard
│   │   └── InterviewPage.tsx # Interview preparation page
│   ├── services/            # API services
│   │   └── api.ts           # API client
│   ├── store/               # State management
│   │   └── useAppStore.ts   # Zustand store
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Utility functions
│   │   └── cn.ts            # Class name utility
│   ├── App.tsx              # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 Features

### 1. Input Page
- Three text input fields for JD, Resume, and Projects
- Form validation
- Character count display

### 2. Loading Page
- Real-time progress updates via SSE
- Step-by-step progress indicator
- Retry mechanism (max 3 attempts)
- Error handling

### 3. Dashboard Page
- Tab-based navigation:
  - **Match Analysis**: Overall match score, detailed breakdowns, strengths/gaps
  - **Candidate Profile**: Ideal candidate requirements
  - **Work Scenario**: Daily activities, work scenarios, KPIs
  - **Projects**: Optimized project summaries
  - **Resume Optimization**: Optimization recommendations with feedback
- Action panel for resume generation
- Export functionality (PDF/DOCX)

### 4. Interview Preparation Page
- Three tabs:
  - **Behavioral Interview**: Self-introduction, storytelling template, top 10 questions
  - **Project Deep-Dive**: Technical questions for selected projects
  - **Business Domain**: Business-related questions

## 🔧 Configuration

### API Base URL

Set in `src/services/api.ts` or via environment variable:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### State Persistence

The app uses localStorage to persist:
- User inputs
- Workflow state
- Interview state
- Final resume
- Current page

## 📝 Usage Flow

1. **Input**: User enters JD, Resume, and optionally Projects
2. **Validation**: Agent 1 validates inputs
3. **Processing**: Agents 2-4 run automatically (with progress updates)
4. **Dashboard**: User reviews results and provides feedback
5. **Resume Generation**: User confirms and generates final resume
6. **Interview Prep**: Agent 5 runs automatically
7. **Interview Page**: User reviews interview preparation materials

## 🐛 Troubleshooting

### Backend Connection Issues

- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `workflow_api.py`
- Verify API endpoints are accessible

### Build Errors

- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

### State Issues

- Clear localStorage: Open browser console and run `localStorage.clear()`
- Reset app state: Use the reset function in the store

## 📦 Dependencies

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Zustand**: State management
- **React Router**: Routing
- **Axios**: HTTP client
- **Lucide React**: Icons

## 🎯 Next Steps (MVP 2)

- [ ] Inline text editing for "further_modify" feedback
- [ ] Real-time collaboration features
- [ ] Export project texts
- [ ] Enhanced error recovery
- [ ] User authentication
- [ ] Data persistence on server
