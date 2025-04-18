from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid

class PokemonCard(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    set_name = models.CharField(max_length=100)
    card_number = models.CharField(max_length=20)
    image_url = models.URLField(blank=True, null=True)
    pokemon_type = models.CharField(max_length=20)
    hp = models.IntegerField(null=True, blank=True)
    card_text = models.TextField(blank=True)
    market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_price_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.set_name} {self.card_number})"

    class Meta:
        unique_together = ['name', 'set_name', 'card_number']

class UserCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection')
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_acquired = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    last_daily_card = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s {self.card.name} x{self.quantity}"

    class Meta:
        unique_together = ['user', 'card']

class MarketplaceListing(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SOLD', 'Sold'),
        ('CANCELLED', 'Cancelled'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.seller.username}'s {self.card.name} listing"

    def save(self, *args, **kwargs):
        # Ensure seller has enough cards to list
        user_card = UserCard.objects.get(user=self.seller, card=self.card)
        if user_card.quantity < self.quantity:
            raise ValueError("Not enough cards in collection to create listing")
        super().save(*args, **kwargs)

class Transaction(models.Model):
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction: {self.buyer.username} bought {self.quantity} {self.listing.card.name} from {self.seller.username}"

    def save(self, *args, **kwargs):
        # Update seller's card quantity
        seller_card = UserCard.objects.get(user=self.seller, card=self.listing.card)
        seller_card.quantity -= self.quantity
        seller_card.save()

        # Update or create buyer's card quantity
        buyer_card, created = UserCard.objects.get_or_create(
            user=self.buyer,
            card=self.listing.card,
            defaults={'quantity': self.quantity}
        )
        if not created:
            buyer_card.quantity += self.quantity
            buyer_card.save()

        # Update listing status if all cards are sold
        if self.listing.quantity == self.quantity:
            self.listing.status = 'SOLD'
            self.listing.save()
        else:
            self.listing.quantity -= self.quantity
            self.listing.save()

        super().save(*args, **kwargs)

class Trade(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_trades')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_trades')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message = models.TextField(blank=True)

    def __str__(self):
        return f"Trade between {self.initiator.username} and {self.recipient.username}"

class TradeOffer(models.Model):
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name='offers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} {self.card.name} from {self.user.username}"

    def save(self, *args, **kwargs):
        # Ensure user has enough cards to offer
        user_card = UserCard.objects.get(user=self.user, card=self.card)
        if user_card.quantity < self.quantity:
            raise ValueError("Not enough cards to offer in trade")
        super().save(*args, **kwargs) 