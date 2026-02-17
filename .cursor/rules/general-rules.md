# General Project Rules

## Project Overview

This is a **Smart CCTV** full-stack application with:
- **Backend**: Python Flask API
- **Frontend**: React + Tailwind CSS
- **Databases**: PostgreSQL (relational) + MongoDB (metadata)

## Development Workflow

1. **Feature Development**:
   - Start with backend (models → repositories → services → controllers)
   - Then implement frontend components
   - Test integration between layers

2. **Code Changes**:
   - Follow existing patterns and architecture
   - Maintain consistency with current codebase
   - Update documentation when adding features

3. **Git Workflow**:
   - Create feature branches
   - Write descriptive commit messages
   - Test before committing

## Code Quality

- **Readability**: Code should be self-documenting
- **Maintainability**: Easy to modify and extend
- **Performance**: Optimize for production use
- **Security**: Never compromise on security

## Documentation

- Update README when adding major features
- Document complex algorithms and business logic
- Keep API documentation up to date
- Include examples in documentation

## Dependencies

- **Backend**: Keep requirements.txt updated
- **Frontend**: Keep package.json updated
- Avoid unnecessary dependencies
- Keep dependencies up to date (security patches)

## Environment Configuration

- Never commit `.env` files
- Use `.env.example` as template
- Document all required environment variables
- Use different configs for dev/staging/prod

## Database Migrations

- Use migrations for schema changes
- Never modify production database directly
- Test migrations on development first
- Backup before migrations

## Security Best Practices

- Validate all user input
- Use parameterized queries
- Implement rate limiting
- Use HTTPS in production
- Keep secrets in environment variables
- Regular security audits

## Testing Strategy

- Write tests for critical functionality
- Test edge cases and error conditions
- Maintain good test coverage
- Run tests before committing

## Performance Optimization

- Profile before optimizing
- Optimize database queries
- Use caching where appropriate
- Minimize API calls
- Optimize images and assets

## Deployment

- Use environment-specific configurations
- Set up proper logging
- Monitor application health
- Set up error tracking
- Use CI/CD pipelines

## Code Review Checklist

- [ ] Follows project architecture
- [ ] No security vulnerabilities
- [ ] Proper error handling
- [ ] Tests included
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] Proper logging
- [ ] Performance considered

