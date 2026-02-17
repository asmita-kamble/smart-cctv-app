# Smart CCTV Frontend

React frontend application for the Smart CCTV surveillance system.

## Technology Stack

- **React 18+** - UI framework
- **React Router v6** - Routing
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

## Setup

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Project Structure

```
src/
├── components/      # Reusable UI components
│   ├── Layout.jsx
│   └── ProtectedRoute.jsx
├── pages/          # Page components
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx
│   ├── Cameras.jsx
│   ├── Alerts.jsx
│   └── Activities.jsx
├── services/       # API service functions
│   ├── authService.js
│   ├── cameraService.js
│   ├── alertService.js
│   ├── activityService.js
│   ├── dashboardService.js
│   └── videoService.js
├── context/        # React context providers
│   └── AuthContext.jsx
├── utils/          # Utility functions
│   └── api.js
├── App.jsx         # Main app component with routing
├── main.jsx        # Entry point
└── index.css       # Global styles
```

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: Overview statistics (admin only)
- **Cameras**: Manage camera configurations
- **Alerts**: View and resolve security alerts
- **Activities**: View detected activities and events
- **Protected Routes**: Route protection based on authentication and roles

## API Configuration

The frontend is configured to connect to the backend API at `http://localhost:5001/api` by default.

You can override this by setting the `VITE_API_URL` environment variable:

```bash
# Create .env file
echo "VITE_API_URL=http://localhost:5001/api" > .env
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use Tailwind CSS for styling
- Keep components small and focused

## Authentication Flow

1. User logs in via `/login`
2. JWT token is stored in localStorage
3. Token is included in API requests via axios interceptor
4. Protected routes check authentication status
5. On 401 errors, user is redirected to login

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:5001/api
```

