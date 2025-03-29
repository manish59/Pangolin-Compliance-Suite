from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
import requests
import json


def login_view(request):
    """
    Handles the login page and form submission
    Provides options for standard login as well as OAuth2 and OpenID
    """
    # If user is already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect("home")

    # Process form submission for standard login
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirect to the page user was trying to access, or home
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")

    # Include OAuth2 and OpenID provider information for the template
    oauth2_providers = getattr(settings, "OAUTH2_PROVIDERS", {})
    openid_providers = getattr(settings, "OPENID_PROVIDERS", {})

    context = {
        "oauth2_providers": oauth2_providers,
        "openid_providers": openid_providers,
    }

    return render(request, "authentication/login.html", context)


def logout_view(request):
    """
    Handles user logout
    """
    logout(request)
    # messages.success(request, 'You have been successfully logged out')
    return redirect("home")


def oauth2_callback(request):
    """
    Handles OAuth2 authentication callback
    """
    code = request.GET.get("code")
    state = request.GET.get("state")

    # Verify state to prevent CSRF
    if state != request.session.get("oauth_state"):
        messages.error(request, "Invalid OAuth state")
        return redirect("authentication:login")

    # Get the provider information based on state
    provider_id = request.session.get("oauth_provider")
    oauth2_providers = getattr(settings, "OAUTH2_PROVIDERS", {})
    provider = oauth2_providers.get(provider_id)

    if not provider:
        messages.error(request, "Unknown OAuth provider")
        return redirect("authentication:login")

    # Exchange code for token
    token_url = provider.get("token_url")
    client_id = provider.get("client_id")
    client_secret = provider.get("client_secret")
    redirect_uri = request.build_absolute_uri(reverse("authentication:oauth2_callback"))

    token_response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    token_data = token_response.json()

    if "error" in token_data:
        messages.error(
            request,
            f"OAuth error: {token_data.get('error_description', token_data['error'])}",
        )
        return redirect("authentication:login")

    # Get user information
    userinfo_url = provider.get("userinfo_url")
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    userinfo_response = requests.get(userinfo_url, headers=headers)
    userinfo = userinfo_response.json()

    # Process user information and login or create account
    # This will depend on your user model and how you map OAuth2 data
    # For this example, we'll just show a basic implementation

    email = userinfo.get("email")
    # You would need to implement a function to get or create a user based on the OAuth data
    # user = get_or_create_oauth_user(userinfo, provider_id)

    # For the sake of the example, we'll just print the info and redirect
    print(f"OAuth2 login successful for {email}")

    # If we had logged in the user:
    # login(request, user)

    return redirect("home")


def openid_callback(request):
    """
    Handles OpenID Connect authentication callback
    """
    code = request.GET.get("code")
    state = request.GET.get("state")

    # Verify state to prevent CSRF
    if state != request.session.get("openid_state"):
        messages.error(request, "Invalid OpenID state")
        return redirect("authentication:login")

    # Get the provider information based on state
    provider_id = request.session.get("openid_provider")
    openid_providers = getattr(settings, "OPENID_PROVIDERS", {})
    provider = openid_providers.get(provider_id)

    if not provider:
        messages.error(request, "Unknown OpenID provider")
        return redirect("authentication:login")

    # Exchange code for token
    token_url = provider.get("token_url")
    client_id = provider.get("client_id")
    client_secret = provider.get("client_secret")
    redirect_uri = request.build_absolute_uri(reverse("authentication:openid_callback"))

    token_response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    token_data = token_response.json()

    if "error" in token_data:
        messages.error(
            request,
            f"OpenID error: {token_data.get('error_description', token_data['error'])}",
        )
        return redirect("authentication:login")

    # For OpenID, we can either validate the ID token or get user info from userinfo endpoint
    # Here, we'll use the userinfo endpoint for consistency with OAuth2

    userinfo_url = provider.get("userinfo_url")
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    userinfo_response = requests.get(userinfo_url, headers=headers)
    userinfo = userinfo_response.json()

    # Process user information and login or create account
    # This will depend on your user model and how you map OpenID data

    email = userinfo.get("email")
    # You would need to implement a function to get or create a user based on the OpenID data
    # user = get_or_create_openid_user(userinfo, provider_id)

    # For the sake of the example, we'll just print the info and redirect
    print(f"OpenID login successful for {email}")

    # If we had logged in the user:
    # login(request, user)

    return redirect("home")
