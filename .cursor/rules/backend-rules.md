# Backend Development Rules

## Architecture Principles

1. **Layered Architecture**: Always maintain the separation between Controllers → Services → Repositories → Models
2. **Single Responsibility**: Each module should have one clear purpose
3. **Dependency Injection**: Services should depend on repositories, not directly on models
4. **Error Handling**: Always return proper HTTP status codes and error messages

## Code Style

- Use Python 3.9+ features
- Follow PEP 8 style guide
- Use type hints where possible
- Document all public methods with docstrings
- Use descriptive variable and function names

## Database Operations

- **Never** perform database operations directly in controllers
- Always use repositories for data access
- Use transactions for multi-step operations
- Handle database errors gracefully

## Authentication & Authorization

- Always use `@require_auth` decorator for protected routes
- Use `@require_admin` for admin-only endpoints
- Never expose password hashes in API responses
- Validate JWT tokens in middleware, not in controllers

## Service Layer Rules

- Services contain business logic only
- Services can call other services
- Services should not directly access database (use repositories)
- Services should return tuples: `(result_dict, status_code)`

## Repository Layer Rules

- Repositories only handle data access
- No business logic in repositories
- Return model objects or None
- Handle database exceptions internally

## Controller Rules

- Controllers are thin - they only handle HTTP requests/responses
- Validate input in controllers
- Call services, not repositories directly
- Return JSON responses with appropriate status codes

## Error Handling

- Use try-except blocks in services
- Return meaningful error messages
- Log errors appropriately
- Never expose internal errors to clients

## Testing

- Write unit tests for services
- Write integration tests for controllers
- Mock external dependencies
- Test error cases

## Security

- Always validate user input
- Sanitize file uploads
- Use parameterized queries (SQLAlchemy handles this)
- Never trust client input
- Check user permissions before operations

## Video Processing

- Process videos asynchronously when possible
- Validate video file types and sizes
- Clean up temporary files
- Handle large files efficiently

## API Design

- Use RESTful conventions
- Return consistent response formats
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Include pagination for list endpoints
- Use query parameters for filtering

