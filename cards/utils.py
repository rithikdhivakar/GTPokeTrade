import requests
import random
from .models import PokemonCard

def get_random_pokemon_card():
    # Get a random page of cards (there are about 20 cards per page)
    page = random.randint(1, 100)
    url = f"https://api.pokemontcg.io/v2/cards?page={page}&pageSize=20"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['data']:
            # Get a random card from the page
            random_card = random.choice(data['data'])
            
            # Create or get the PokemonCard
            card, created = PokemonCard.objects.get_or_create(
                name=random_card['name'],
                set_name=random_card['set']['name'],
                card_number=random_card['number'],
                defaults={
                    'image_url': random_card['images']['large'],
                    'pokemon_type': random_card.get('types', ['Unknown'])[0],
                    'hp': random_card.get('hp'),
                    'card_text': random_card.get('flavorText', ''),
                    'market_price': random_card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0)
                }
            )
            return card
    except Exception as e:
        print(f"Error fetching random card: {e}")
        return None 