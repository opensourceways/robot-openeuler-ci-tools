from rest_framework import permissions
  

class ReviewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        data = request.data
        hook_name = data.get('hook_name', '')
        action = data.get('action', '')
        if not hook_name or not action:
            return False
        if hook_name not in ['merge_request_hooks', 'note_hooks']:
            return False
        if action not in ['open', 'comment', 'update']:
            return False
        return True

