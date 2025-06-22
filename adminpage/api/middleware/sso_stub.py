from django.utils.deprecation import MiddlewareMixin

class SSOMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.current_student = {
            "email": "student@example.com",
            "id": 123,
            "name": "Test Student"
        }
