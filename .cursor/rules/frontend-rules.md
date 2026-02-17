# Frontend Development Rules

## Technology Stack

- **Framework**: React 18+
- **Styling**: Tailwind CSS
- **State Management**: React Hooks (useState, useContext, useReducer)
- **HTTP Client**: Axios or Fetch API
- **Routing**: React Router v6+

## Component Structure

- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use TypeScript for type safety (if applicable)

## File Organization

```
src/
├── components/     # Reusable UI components
├── pages/         # Page-level components
├── services/      # API service functions
├── hooks/         # Custom React hooks
├── context/       # React context providers
├── utils/         # Utility functions
└── constants/     # Constants and configuration
```

## Code Style

- Use functional components
- Use arrow functions for component definitions
- Use destructuring for props
- Use meaningful component and variable names
- Follow React naming conventions (PascalCase for components)

## State Management

- Use `useState` for local component state
- Use `useContext` for global state (auth, theme, etc.)
- Use `useReducer` for complex state logic
- Avoid prop drilling - use context when needed

## API Integration

- Create service files for each API endpoint group
- Use async/await for API calls
- Handle loading and error states
- Store JWT tokens securely (httpOnly cookies or localStorage)
- Include token in Authorization header: `Bearer <token>`

## Authentication

- Protect routes with authentication checks
- Redirect to login if not authenticated
- Store user info in context
- Handle token expiration gracefully

## Styling

- Use Tailwind CSS utility classes
- Create custom components for repeated patterns
- Use responsive design (mobile-first)
- Maintain consistent spacing and colors

## Error Handling

- Display user-friendly error messages
- Handle network errors gracefully
- Show loading states during API calls
- Validate forms before submission

## Performance

- Use React.memo for expensive components
- Lazy load routes with React.lazy
- Optimize images
- Avoid unnecessary re-renders

## Accessibility

- Use semantic HTML
- Include ARIA labels where needed
- Ensure keyboard navigation works
- Maintain proper color contrast

## Testing

- Write unit tests for utilities
- Write component tests with React Testing Library
- Test user interactions, not implementation details

