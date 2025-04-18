from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('marketplace/', views.marketplace, name='marketplace'),
    path('marketplace/create/<uuid:card_id>/', views.create_listing, name='create_listing'),
    path('marketplace/my-listings/', views.my_listings, name='my_listings'),
    path('trading/', views.trading, name='trading'),
    path('trading/create/<int:user_id>/', views.create_trade, name='create_trade'),
    path('trading/<int:trade_id>/', views.respond_to_trade, name='respond_to_trade'),
] 