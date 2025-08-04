from django.http import JsonResponse

def root_welcome(request):
    """Root welcome endpoint"""
    return JsonResponse({
        'message': 'Welcome to Drop Me RVM Backend API',
        'version': '1.0.0',
        'description': 'AI-driven Recycling Vending Machine platform for Egypt & MEA',
        'motto': 'Your waste can be your card for your supplies',
        'api_endpoints': '/api/',
        'admin_panel': '/admin/',
        'documentation': 'See README.md for complete API documentation'
    })
