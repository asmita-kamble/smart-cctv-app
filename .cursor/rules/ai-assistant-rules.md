# AI Assistant Rules for Smart CCTV Project

## Context Awareness

When working on this project, the AI assistant should:

1. **Understand the Architecture**:
   - Recognize the layered architecture (Controllers → Services → Repositories → Models)
   - Maintain separation of concerns
   - Follow existing patterns

2. **Know the Tech Stack**:
   - Backend: Python Flask, SQLAlchemy, PostgreSQL, MongoDB
   - Frontend: React, Tailwind CSS
   - Authentication: JWT tokens
   - Video Processing: OpenCV, face_recognition

3. **Respect Project Structure**:
   - Place files in correct directories
   - Follow naming conventions
   - Maintain module organization

## Code Generation Guidelines

### When Creating New Features

1. **Backend Features**:
   - Start with model (if new entity needed)
   - Create repository for data access
   - Implement service for business logic
   - Add controller for API endpoint
   - Register route in routes.py

2. **Frontend Features**:
   - Create service function for API calls
   - Build reusable components
   - Create page component
   - Add routing if needed

### When Modifying Existing Code

- Maintain existing patterns
- Don't break existing functionality
- Update related tests
- Keep backward compatibility when possible

## Common Patterns to Follow

### Backend API Response Format

```python
# Success response
return jsonify({
    'message': 'Operation successful',
    'data': result_dict
}), 200

# Error response
return jsonify({
    'error': 'Error message',
    'details': 'Additional details'
}), status_code
```

### Service Method Pattern

```python
@staticmethod
def method_name(param1, param2):
    """
    Method description.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Tuple of (result_dict, status_code)
    """
    try:
        # Business logic
        result = ...
        return result, 200
    except Exception as e:
        return {'error': str(e)}, 500
```

### Controller Endpoint Pattern

```python
@bp.route('/endpoint', methods=['POST'])
@require_auth
def endpoint_name(current_user):
    """Endpoint description."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate input
    # Call service
    result, status_code = Service.method(data)
    return jsonify(result), status_code
```

## What NOT to Do

1. **Don't** bypass the repository layer
2. **Don't** put business logic in controllers
3. **Don't** hardcode configuration values
4. **Don't** expose sensitive information
5. **Don't** create circular dependencies
6. **Don't** ignore error handling
7. **Don't** skip input validation

## When to Ask Questions

- If requirements are unclear
- If there are conflicting requirements
- If a decision affects architecture
- If security implications are unclear

## Code Review Focus Areas

When reviewing or suggesting code:

1. **Security**: Check for vulnerabilities
2. **Performance**: Identify bottlenecks
3. **Maintainability**: Ensure code is readable
4. **Consistency**: Match existing patterns
5. **Error Handling**: Proper exception handling
6. **Testing**: Consider testability

## Documentation Standards

- Document all public methods
- Include parameter descriptions
- Explain return values
- Add usage examples for complex functions
- Update README for new features

## Testing Considerations

- Suggest unit tests for services
- Suggest integration tests for controllers
- Test error cases
- Test edge cases
- Mock external dependencies

