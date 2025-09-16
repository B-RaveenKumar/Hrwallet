from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    """
    Home view that redirects to appropriate dashboard
    """
    return render(request, 'base.html')
