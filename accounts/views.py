from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, UserProfileForm
from cards.utils import get_random_pokemon_card
from cards.models import UserCard
from datetime import date

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Get a random card for the new user
            random_card = get_random_pokemon_card()
            if random_card:
                # Create a UserCard entry for the new user
                UserCard.objects.create(
                    user=user,
                    card=random_card,
                    quantity=1,
                    last_daily_card=date.today()
                )
                messages.success(request, f'Account created successfully! You received a {random_card.name} card!')
            else:
                messages.success(request, 'Account created successfully!')
            
            return redirect('home.index')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/signup.html', {
        'form': form,
        'template_data': {
            'title': 'Sign Up - PokeTrade'
        }
    })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if user has received a card today
                today = date.today()
                user_cards = UserCard.objects.filter(user=user)
                
                if not user_cards.exists() or not any(card.last_daily_card == today for card in user_cards):
                    # Get a random card for the user
                    random_card = get_random_pokemon_card()
                    if random_card:
                        # Create or update UserCard entry
                        user_card, created = UserCard.objects.get_or_create(
                            user=user,
                            card=random_card,
                            defaults={
                                'quantity': 1,
                                'last_daily_card': today
                            }
                        )
                        if not created:
                            user_card.quantity += 1
                            user_card.last_daily_card = today
                            user_card.save()
                        
                        messages.success(request, f'Welcome back, {username}! You received a daily {random_card.name} card!')
                    else:
                        messages.success(request, f'Welcome back, {username}!')
                else:
                    messages.success(request, f'Welcome back, {username}!')
                
                return redirect('home.index')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'template_data': {
            'title': 'Login - PokeTrade'
        }
    })

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home:index')

@login_required
def profile(request, user_id=None):
    # If user_id is provided, show that user's profile, otherwise show the current user's profile
    profile_user = get_object_or_404(User, id=user_id) if user_id else request.user
    user_cards = profile_user.collection.all().select_related('card')
    
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'user_cards': user_cards,
        'template_data': {
            'title': f"{profile_user.username}'s Profile - PokeTrade"
        }
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'template_data': {
            'title': 'Edit Profile - PokeTrade'
        }
    }) 