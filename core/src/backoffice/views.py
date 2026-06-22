from django.shortcuts import render
from .decorators import superuser_required


@superuser_required
def overview(request):
    return render(request, 'backoffice/overview.html', {})
