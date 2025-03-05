from django.shortcuts import render

def home(request):
    """
    View function for the home page.
    Renders the home.html template.
    """
    return render(request, 'home/home.html')

def login(request):
    return (request, 'home/login.html', {})