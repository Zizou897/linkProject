from django.shortcuts import render
from .decorators import superuser_required


@superuser_required
def overview(request):
    return render(request, 'backoffice/overview.html', {'active': 'overview'})


@superuser_required
def users_list(request):
    return render(request, 'backoffice/stub.html', {'active': 'users', 'heading': 'Utilisateurs'})


@superuser_required
def journal(request):
    return render(request, 'backoffice/stub.html', {'active': 'journal', 'heading': 'Journal'})


@superuser_required
def health(request):
    return render(request, 'backoffice/stub.html', {'active': 'health', 'heading': 'Santé technique'})
