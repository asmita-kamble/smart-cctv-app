# Cursor Rules Directory

This directory contains project-specific rules and guidelines for the Smart CCTV application.

## Rules Files

### `.cursorrules`
Main rules file that Cursor IDE reads automatically. Contains high-level project principles and quick reference.

### `rules/backend-rules.md`
Detailed rules for backend development:
- Architecture principles
- Code style guidelines
- Database operation rules
- Authentication & authorization patterns
- Service, repository, and controller rules
- Error handling standards
- Security best practices

### `rules/frontend-rules.md`
Detailed rules for frontend development:
- React component structure
- State management patterns
- API integration guidelines
- Styling with Tailwind CSS
- Error handling
- Performance optimization
- Accessibility standards

### `rules/general-rules.md`
General project rules applicable to both frontend and backend:
- Development workflow
- Code quality standards
- Documentation requirements
- Security best practices
- Testing strategy
- Deployment guidelines

### `rules/ai-assistant-rules.md`
Rules specifically for AI assistants working on this project:
- Context awareness guidelines
- Code generation patterns
- Common patterns to follow
- What NOT to do
- When to ask questions
- Code review focus areas

## Usage

These rules help maintain consistency across the codebase and guide development decisions. When working on the project:

1. Follow the architecture patterns defined in the rules
2. Refer to specific rule files when implementing features
3. Update rules when project standards change
4. Use rules as a reference for code reviews

## How Cursor Uses These Rules

- `.cursorrules` is automatically read by Cursor IDE
- Rules in `.cursor/rules/` provide detailed context
- AI assistants use these rules to generate code that follows project standards
- Rules help maintain consistency across the codebase

