from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

limit = 10

def get_pokemon_list(offset=0, limit=10):
    url = f"https://pokeapi.co/api/v2/pokemon/?offset={offset}&limit={limit}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()  
        pokemon_list = data.get("results", [])
        all_poke_count = data['count']
        return pokemon_list, int(all_poke_count / limit + 1)
    else:
        print(f"Error: {response.status_code}")
        return [], 0


def get_page_list(cur_page=1, final_page=1):
    left = cur_page - 3 if cur_page >= 4 else 1
    right = cur_page + 3 if final_page - cur_page >= 3 else final_page
    return list(range(left, right + 1))


@app.route('/')
def pokemons():
    try:
        page = int(request.args.get('page')) if request.args.get('page') else 1
    except ValueError:
        page = 1

    offset = (page - 1) * limit 
 
    pokemon_list, page_count = get_pokemon_list(offset, limit)
    
    return render_template("list.html", 
                           pokemons=pokemon_list, 
                           page_list=get_page_list(page, page_count), 
                           current=page, 
                           final_page=page_count)


@app.route("/search")
def search():
    pokemon_name = request.args.get('search_string')
    if pokemon_name == "":
        return redirect(url_for("pokemons"))
    else:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                "id": data["id"],
                "name": data["name"]
            }
    
            return render_template("list.html", pokemons=result, search_string=pokemon_name)
        else:
            return render_template("list.html", pokemons=[], search_string=pokemon_name)


if __name__ == '__main__':
    app.run(port=8000, debug=True)
    