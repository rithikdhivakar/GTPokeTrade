from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PokemonCard, UserCard, MarketplaceListing, User, Trade, TradeOffer
from .forms import ListingForm
from django.db.models import Q

def marketplace(request):
    active_listings = MarketplaceListing.objects.filter(status='ACTIVE').select_related('card', 'seller')
    return render(request, 'cards/marketplace.html', {
        'listings': active_listings,
        'template_data': {
            'title': 'Marketplace - PokeTrade'
        }
    })

@login_required
def create_listing(request, card_id):
    card = get_object_or_404(PokemonCard, uid=card_id)
    user_card = get_object_or_404(UserCard, user=request.user, card=card)
    
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            price = form.cleaned_data['price']
            
            if quantity > user_card.quantity:
                messages.error(request, "You don't have enough cards to list that quantity.")
            else:
                listing = MarketplaceListing.objects.create(
                    seller=request.user,
                    card=card,
                    quantity=quantity,
                    price=price,
                    description=form.cleaned_data['description']
                )
                messages.success(request, f'Successfully listed {quantity} {card.name} card(s) for sale!')
                return redirect('cards.marketplace')
    else:
        form = ListingForm(initial={
            'quantity': 1,
            'price': card.market_price if card.market_price else 0
        })
    
    return render(request, 'cards/create_listing.html', {
        'form': form,
        'card': card,
        'user_card': user_card,
        'template_data': {
            'title': f'List {card.name} for Sale - PokeTrade'
        }
    })

@login_required
def my_listings(request):
    listings = MarketplaceListing.objects.filter(seller=request.user).select_related('card')
    return render(request, 'cards/my_listings.html', {
        'listings': listings,
        'template_data': {
            'title': 'My Listings - PokeTrade'
        }
    })

@login_required
def trading(request):
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id)
    
    # Get pending trades where user is either initiator or recipient
    pending_trades = Trade.objects.filter(
        Q(initiator=request.user) | Q(recipient=request.user),
        status='PENDING'
    ).select_related('initiator', 'recipient').prefetch_related('offers__card')

    return render(request, 'cards/trading.html', {
        'users': users,
        'pending_trades': pending_trades,
        'template_data': {
            'title': 'Trading - PokeTrade'
        }
    })

@login_required
def create_trade(request, user_id):
    recipient = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Create the trade
        trade = Trade.objects.create(
            initiator=request.user,
            recipient=recipient,
            message=request.POST.get('message', '')
        )
        
        # Add cards from initiator
        for key, value in request.POST.items():
            if key.startswith('initiator_card_'):
                card_id = key.split('_')[2]
                quantity = int(value)
                if quantity > 0:
                    card = get_object_or_404(PokemonCard, uid=card_id)
                    TradeOffer.objects.create(
                        trade=trade,
                        user=request.user,
                        card=card,
                        quantity=quantity
                    )
        
        # Add cards from recipient
        for key, value in request.POST.items():
            if key.startswith('recipient_card_'):
                card_id = key.split('_')[2]
                quantity = int(value)
                if quantity > 0:
                    card = get_object_or_404(PokemonCard, uid=card_id)
                    TradeOffer.objects.create(
                        trade=trade,
                        user=recipient,
                        card=card,
                        quantity=quantity
                    )
        
        messages.success(request, 'Trade offer sent successfully!')
        return redirect('cards.trading')
    
    # Get cards from both users
    initiator_cards = UserCard.objects.filter(user=request.user).select_related('card')
    recipient_cards = UserCard.objects.filter(user=recipient).select_related('card')
    
    return render(request, 'cards/create_trade.html', {
        'recipient': recipient,
        'initiator_cards': initiator_cards,
        'recipient_cards': recipient_cards,
        'template_data': {
            'title': f'Create Trade with {recipient.username} - PokeTrade'
        }
    })

@login_required
def respond_to_trade(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id, recipient=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            # Update trade status
            trade.status = 'ACCEPTED'
            trade.save()
            
            # Process the trade
            for offer in trade.offers.all():
                # Remove cards from offering user
                offering_user_card = UserCard.objects.get(user=offer.user, card=offer.card)
                offering_user_card.quantity -= offer.quantity
                offering_user_card.save()
                
                # Add cards to receiving user
                receiving_user = trade.initiator if offer.user == trade.recipient else trade.recipient
                receiving_user_card, created = UserCard.objects.get_or_create(
                    user=receiving_user,
                    card=offer.card,
                    defaults={'quantity': offer.quantity}
                )
                if not created:
                    receiving_user_card.quantity += offer.quantity
                    receiving_user_card.save()
            
            messages.success(request, 'Trade accepted successfully!')
        elif action == 'reject':
            trade.status = 'REJECTED'
            trade.save()
            messages.info(request, 'Trade rejected.')
        elif action == 'cancel':
            if trade.initiator == request.user:
                trade.status = 'CANCELLED'
                trade.save()
                messages.info(request, 'Trade cancelled.')
            else:
                messages.error(request, 'You can only cancel trades you initiated.')
        
        return redirect('cards.trading')
    
    return render(request, 'cards/trade_details.html', {
        'trade': trade,
        'template_data': {
            'title': f'Trade Details - PokeTrade'
        }
    }) 