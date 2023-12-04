from models import Fight
import random
from datetime import datetime, timedelta

def generate_random_date(start_date, end_date):
    time_delta = end_date - start_date
    random_days = random.randint(0, time_delta.days)
    random_time = timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return start_date + timedelta(days=random_days) + random_time

def data_generation(db, num_fight=10):
    pokemons = ['bulbasaur', 'ivysaur', 'venusaur', 'charmander', 'mantyke', 'jynx', 'slowking']

    for n in range(num_fight):
        select_pokemon = random.choice(pokemons)
        vs_pokemon = random.choice([poke for poke in pokemons if poke != select_pokemon])
        
        start_date = datetime(2023, 11, 20)
        end_date = datetime.now()
        
        random_date = generate_random_date(start_date, end_date)
        
        fight_row = Fight(select_pokemon=select_pokemon,
                        vs_pokemon=vs_pokemon,
                        win=random.choice([True, False]),
                        rounds=random.choice(list(range(1, 5))),
                        date_time=random_date)
        db.session.add(fight_row)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
