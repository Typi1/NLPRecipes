from bs4 import BeautifulSoup
import json
import requests

def get_soup(url:str):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

def get_dict(url:str):
    recipe_html = get_soup(url)
    recipe_dict = None
    candidate_json = recipe_html.find_all("script", {"type": "application/ld+json"})
    for candidate in candidate_json:
        r = json.loads(candidate.text)
        # print(r)
        try:
            if r["@type"] == "Recipe":
                recipe_dict = r
        except:
            if r[0]["@type"] == ["Recipe"]:
                recipe_dict = r
    if not recipe_dict:
        print("Recipe not found!")
        return None
    else:
        return recipe_dict

def get_recipe(url):
    recipe = get_dict(url)
    # print(recipe)
    try:
        ingredients = recipe["recipeIngredient"]
        steps = recipe["recipeInstructions"]
    except:
        ingredients = recipe[0]["recipeIngredient"]
        steps = recipe[0]["recipeInstructions"]
    instructions = []
    for step in steps:
        if "text" in step:
            instructions.append(step["text"])
    print(ingredients)
    print(instructions)
    return [ingredients, instructions]

def main():
    url = 'https://tasty.co/recipe/fried-egg-pizza'
    get_recipe(url)

if __name__ == "__main__":
    main()