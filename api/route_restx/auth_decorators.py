from functools import wraps
from typing import Callable, List, Union, Dict, Any, TypeVar, cast
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_restx import abort

F = TypeVar('F', bound=Callable[..., Any])

def role_required(allowed_roles: Union[str, List[str]]) -> Callable[[F], F]:
    """
    A decorator that checks if the user has any of the required roles.
    
    Args:
        allowed_roles: A list of roles or a single role string that is allowed to access the endpoint
    
    Usage:
        @role_required('admin')
        def admin_only_endpoint():
            ...
            
        @role_required(['employer', 'admin'])
        def employer_or_admin_endpoint():
            ...
    """
    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # First verify the JWT is valid
            verify_jwt_in_request()
            
            # Get the identity from JWT
            identity: Dict[str, Any] = get_jwt_identity()
            
            # Check if identity is valid and contains type/role
            role_field = 'role' if 'role' in identity else 'type'
            if not identity or role_field not in identity:
                abort(401, 'Invalid token or missing role information')
            
            # Convert allowed_roles to list if it's a string
            roles: List[str] = allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]
            
            # Check if user's role is in the allowed roles
            if identity[role_field] not in roles:
                abort(403, f'Access denied. This endpoint requires one of these roles: {", ".join(roles)}')
            
            # If role check passed, execute the decorated function
            return fn(*args, **kwargs)
        return cast(F, wrapper)
    return decorator

def employee_required(fn: F) -> F:
    """
    A shortcut decorator that allows only employees to access the endpoint
    """
    @wraps(fn)
    @role_required('employee')
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)
    return cast(F, wrapper)

def employer_required(fn: F) -> F:
    """
    A shortcut decorator that allows only employers to access the endpoint
    """
    @wraps(fn)
    @role_required('employer')
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)
    return cast(F, wrapper)

def admin_required(fn: F) -> F:
    """
    A shortcut decorator that allows only admins to access the endpoint
    """
    @wraps(fn)
    @role_required('admin')
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)
    return cast(F, wrapper)