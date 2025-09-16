from .models import Company


def company_context(request):
    """
    Add company information to all templates
    """
    company = None
    current_date = None

    try:
        # Get the first company as default (handle database errors gracefully)
        company = Company.objects.first()

        # If no company exists, create a default one
        if not company:
            company, created = Company.objects.get_or_create(
                name='Demo Company',
                defaults={
                    'address': '123 Business Street',
                    'phone': '+1-555-0123',
                    'email': 'info@demo.com',
                }
            )
    except Exception as e:
        # If there's any database issue, continue without company
        company = None

    try:
        # Safely get current date
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_date = getattr(request.user, 'date_joined', None)
    except Exception:
        current_date = None

    return {
        'company': company,
        'current_date': current_date,
    }
