from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import json
import requests
import transformers as tra
import re

## FUNCTIONS FOR WEBSCRAPING
def get_soup(url:str):
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")

def get_dict(url:str):
    # in case the user does not submit a link
    try:
        recipe_html = get_soup(url)
    except:
        print("This is not a valid link! Please provide a URL.\n")
        return None

    recipe_dict = None
    d_type = None
    
    # in case the link is not a recipe that fits the format we are scrapping for
    try:
        candidate_json = recipe_html.find_all("script", {"type": "application/ld+json"})
    except:
        print("Recipe not found! Please provide a different URL.\n")
        return None

    for candidate in candidate_json:
        r = json.loads(candidate.text)
        # print(type(r))
        if isinstance(r, dict):
            if r["@type"] == "Recipe":
                recipe_dict = r
                d_type = dict
                break
        elif isinstance(r, list):
            if r[0]["@type"][0] == "Recipe":
                recipe_dict = r
                d_type = list
                break
            elif r[0]["@type"] == "Recipe":
                recipe_dict = r
                d_type = list
                break
    return [recipe_dict, d_type]

def get_recipe(url:str):
    recipe = get_dict(url)

    # get_dict will return None if given a faulty link, so get_recipe will also return None
    if recipe == None:
        return None

    # if get_dict recieves a link that doesn't contain a recipe we can scrape, say that to the user and return None
    try: 
        try: 
            x = recipe[0]["recipeIngredient"]
        except:
            x = recipe[0][0]["recipeIngredient"]
    except:
        print("Recipe not found! Please provide a different URL.\n")
        return None

    if recipe[0]:
        if recipe[1] == dict:
            ingredients = recipe[0]["recipeIngredient"]
            name = recipe[0]["name"] # ASK SEAN TO EDIT THIS
            if "itemListElement" in recipe[0]["recipeInstructions"]:
                steps = recipe[0]["recipeInstructions"]["itemListElement"]
            else:
                steps = recipe[0]["recipeInstructions"]
        elif recipe[1] == list:
            ingredients = recipe[0][0]["recipeIngredient"]
            name = recipe[0][0]["name"] # ASK SEAN TO EDIT THIS
            if "itemListElement" in recipe[0][0]["recipeInstructions"][0]:
                steps = recipe[0][0]["recipeInstructions"][0]["itemListElement"]
            else:
                steps = recipe[0][0]["recipeInstructions"]
    instructions = []
    for step in steps:
        if "text" in step:
            instructions.append(step["text"])
            
    return [ingredients, instructions, name]


## LISTS FOR ZERO SHOT AND DICTIONARIES FOR HARD CODED OPERATIONS
seq_ing = [    
    "Can you share the list of ingredients?",    
    "What are the ingredients used?",    
    "Could you please provide the ingredients?",    
    "May I know what the ingredients are?",    
    "What's in this dish?",    
    "Ingredients, please?",    
    "What goes into making this?",   
    "Can you show me the ingredient list?",    
    "Let me see the list of ingredients.",    
    "Can we go to the ingredient list?",
    "I'd love to know what ingredients are in this recipe.",
    "Can you tell me the components of this dish?",
    "What are the constituent parts of this meal?",
    "Please share the list of components for this recipe.",
    "Could you provide me with a list of what's in this?",
    "May I have a rundown of the ingredients?",
    "What are the contents of this dish?",
    "I'm curious about what goes into making this, could you tell me?",
    "Do you have a list of what's in this recipe?",
    "Can you let me know what ingredients are used in this dish?"]

seq_num = [
    "Has a number",
    "Asks to move on to a numbered step",
    "Has numeric label",      
    "Has numbered steps?",    
    "There is a step with a number",    
    "numbered item"]

seq_next = [
    "Proceed to the following step.",
    "Let's move on to the next step.",    
    "Next step Please",
    "Can we move forward with the next step?",    
    "Advance to the next step.",    
    "Let's continue with the next step.",    
    "Can we continue reading the recipe steps?",    
    "Move on to the next step.",    
    "Tell me the following step.",    
    "Continue reading the recipe steps.",
    "Next step.",    
    "Proceed to the subsequent step.",    
    "Let's advance to the following step.",    
    "What's the subsequent step in the recipe?",   
    "Can you guide me to the next step?",    
    "What comes after this step?",    
    "Let's move forward with the following step.",    
    "What's the next instruction in the recipe?",    
    "What's the next step on our recipe?",    
    "Can we move on to the next recipe part?"
]

seq_prev = [    
    "Return to the previous step",    
    "Step back to the last instruction",    
    "Go back one step",    
    "What was the last step again?",    
    "Revisit the previous step",
    "Repeat the last step",    
    "Move back to the last step",    
    "Can we go back one step?",    
    "Let's backtrack to the previous step",    
    "Reverse to the previous step",    
    "Retreat to the last instruction",
    "Let's step back to the previous instruction",    
    "Can we move back to the last step?",    
    "Let's go back one step",    
    "Let's revisit the previous instruction",    
    "Take a step back to the last step",    
    "Can we backtrack to the previous instruction?",    
    "Return to the preceding step",    
    "Let's reverse to the last instruction",       
    "Can we step back one instruction?"]

seq_rep = [
    "Repeat the current step please.",
    "Repeat the recipe step",
    "Could you say the current step again?",  
    "Please repeat the current instruction.",    
    "Can you say that step again?",    
    "Repeat the current recipe step.",    
    "Say the current step once more please.",    
    "Could you repeat the current instruction?",       
    "Let's repeat the current step.",    
    "Can you restate the current step?",    
    "Could you go over the current step again?",    
    "Repeat the current step one more time.",          
    "Say the current step one more time, please.",          
     "Could you go over the current step once more?",    
     "Can you restate the current instruction?",    
     "Please repeat the current step.",    
     "Can you repeat the current step, please?",    
     "Say the current instruction again, please.",
     "Repeat the step.",
     "Say the last recipe step again."]
     
seq_other_q = [    
    "Question that starts with 'How to'",
    "Question that starts with 'How do I use'",
    "Question that starts with 'How long'", 
    "Question that starts with 'What is a'",  
    "Vague Cooking Question",
    "Specific Cooking Question",
    "Cooking Question",
    # I added one of the subistitution questions here
    "Question about substitution",   
]

seq_sub = [    
    "Question about replacement",    
    "Question about swapping",    
    "Question about replacing",    
    "Question about exchanging",       
    "Question about switching",    
    "Question about altering",
    "Question about substitution",
    "Question about using an alternative",
    "Question about changing",
    "Question about finding a replacement",
    ]

word_num_dic = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20
}

word_place_dic = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20
}


## THIS IS THE CLASS THAT CONTAINS ALL OF THE CODE FOR CONVERSATION
## CREATING AN INSTANCE OF IT STARTS A CONVERSATION
class RecipeBot():
    def __init__(self):
        # giving the bot a name
        self.name = "MealMaster"

        # asking for the url
        r = None
        print(f"{self.name}: Hey there! I am the MealMaster, here to help you with all your cooking needs!")
        print(f"{self.name}: I can answer all sorts of questions to help you through a recipe! Just be advised, on average I take 15 seconds to respond.")
        print(f"{self.name}: Ready to cook a recipe? Please provide a URL.\n")
        while r == None:
            url = input("User: ")
            print("\n")
            r = get_recipe(url)
        
        self.ingredients = r[0]
        self.steps = r[1]
        self.recipe_name = r[2]
        
        print(f"{self.name}: Thank you, please wait a moment.")

        # variable for what step the bot is in the recipe
        self.curr_step = 0
        
        # zero shot classification pipeline
        self.zero_shot_pipe = tra.pipeline(task="zero-shot-classification",model="facebook/bart-large-mnli")

        # starting the conversation with the user
        print(f"{self.name}: Alright, '{self.recipe_name}' has been booted up! What do you want to do?")
        self.begin_conversation()

    def begin_conversation(self):
        r = None
        # This loop forces the user to either start with the ingredient list or recipe steps
        while r != '1' and r != '2':
            print(f"{self.name}: Type '1' to go over ingredients list or type '2' to go over the recipe steps.\n")

            r = input("User: ")
            print("\n")
            
            if r != '1' and r != '2': 
                print(f"{self.name}: Sorry, '{r}' is not a valid input")


        if r == '1': 
            # tells the bot to print the recipe steps. The "True" input is so the computer can diferentiate betweeen
            return self.print_ingredients(True)
        else:
            # tells the bot to print the step curr_step indexes
            return self.print_step()
    
    # This function controls the flow of conversation. After the bot has answered a user request, this function should be called.
    def default(self, state = None):
        # if state is "confused", say a generic sentetence that allows the bot to try again at the command
        if state == "confused":
            print(f"{self.name}: Sorry, could you re-phrase that?\n")
            r = input("User: ")
            print("\n")
            if not r: r = "go_to_nothing_state" # when the user types nothing, use this string to go to "nothing" state in self.default()
            self.interpret(r)

        # state will equal "done" if all recipe steps have been printed. If that's the case, ask the usr for any last requests and finish the program if otherwise
        elif state == "done":
            q = "Looks like we went through the entire recipe, anything else I can do for you?\n"
            print(f"{self.name}: {q}")
            
            r = input("User: ")
            print("\n")
            if not r: r = "No thank you"

            zs_label = self.zs_with_q(q, r, ["User says no or thank you", "User asks a Question", "User says an Imperative sentence", "User says yes"])
            if zs_label == "User says no or thank you":
                print(f"{self.name}: Sounds good, enjoy your meal!\n")
                return
            else:
                return self.interpret(r)

        # state will equal this if the user didn't type anything
        elif state == "go_to_nothing_state":
            print(f"{self.name}: Sorry, I couldn't hear you. Could you go again?\n")
            r = input("User: ")
            print("\n")
            if not r: r = "go_to_nothing_state" # when the user types nothing, use this string to go to "nothing" state in self.default()
            self.interpret(r)

        # this is the general neutral state. Just asks for user input and calls interpret function
        else:
            print(f"{self.name}: What would you like me to do next?\n")
            r = input("User: ")
            print("\n")
            if not r: r = "go_to_nothing_state" # when the user types nothing, use this string to go to "nothing" state in self.default()

            self.interpret(r)
        return

    # This function takes user input and decides what the bot has to do
    # The bot has certain abilities, this function is supposed to map user input to the approriate function that does the requested task
    # If the user's input either can't be interpreted, asks for an impossible task, or complete's the recipe steps, the function calls self.default 
    def interpret(self, user_input):
        # in case the user doesn't type anything, user_input will be "go_to_nothing_state", so go to "go_to_nothing_state"
        if user_input == "go_to_nothing_state":
            return self.default("go_to_nothing_state")
        # calculate the zero shot similarity score
        zs_scores = {
            "ing_score": self.zs_add_scores(user_input, seq_ing),
            "num_score": self.zs_add_scores(user_input, seq_num),
            "next_score": self.zs_add_scores(user_input, seq_next),
            "prev_score": self.zs_add_scores(user_input, seq_prev),
            "rep_score": self.zs_add_scores(user_input, seq_rep),
            "other_question_score": self.zs_add_scores(user_input, seq_other_q)
        }

        # find the biggest, if the biggest is smaller than 10, go to "confused" state in the self.default function
        zs_best = "ing_score"
        for k in zs_scores.keys():
            if zs_scores[k] > zs_scores[zs_best]:
                zs_best = k
        
        if zs_scores[zs_best] < 10 and zs_best != "other_question_score":
            return self.default("confused")
        
         # If the user asks to go to a specific step
         # in this case, the best performance was achieved when we ignored the best scorer and 
         # only considered if the score for "num_score" was above a certain threshold
        elif zs_scores["num_score"] > 10:
            # extracting the number from the text
            num = re.findall("[0-9]+", user_input)
            if num:
                num = int(num[0])
            else:
                #user_input does not have a number, so let's look numner words like "three" and "third"
                for k in word_place_dic.keys():
                    if k in user_input:
                        num = word_place_dic[k]
                        break
                if not num:
                    for k in word_num_dic.keys():
                        if k in user_input:
                            num = word_num_dic[k]
                            break 
                # if number is still not found, go to "confused" state in default
                if not num:
                    return self.default("confused")
            
            # Checks if the requested step number exists
            if num > len(self.steps):
                print(f"{self.name}: Sorry, I can't do that. This recipe only has {len(self.steps)} steps")
                return self.default()
            elif num < 1:
                print(f"{self.name}: Sorry, I can't do that. This recipe's first step is step #1")
                return self.default()
            # If step number exists, update current step and print it
            else:
                self.curr_step = num - 1
                return self.print_step()
            
        elif zs_best == "next_score":
            # Checks to see if there is a next step
            if self.curr_step + 2 > len(self.steps):
                # If not, that means we are done reading the recipe steps and can move on to the "done" state of the self.default function
                print(f"{self.name}: Sorry, I can't do that. Step #{self.curr_step + 1} is the last step of the recipe.")
                return self.default("done")
            # If so, updates current step and calls the function that prints the current step
            else:
                self.curr_step += 1
                return self.print_step()
       
        elif zs_best == "prev_score":
            # Checks to see if there is a previous step, if not asks the user for new input by calling self.default()
            if self.curr_step - 1 < 0:
                print(f"{self.name}: Sorry, I can't do that. There's no previous step since we are at the first step of the recipe")
                return self.default()
            else:
                # If there is a previous step, update current step and print it
                self.curr_step -= 1
                return self.print_step()

        # If the user asks to repeat the current step, print it
        elif zs_best == "rep_score":
            self.print_step()
        
        # if the user requests to see the ingredient list, print the ingredients list
        elif zs_best == "ing_score":
            return self.print_ingredients()
        
        #NEED TO CHANGE THIS
        # if the user asks a "how to" question, scrape information from the web and print it.
        elif zs_best == "other_question_score":
            # checking to see if the question is about subistitution
            sub_score = self.zs_add_scores(user_input, seq_sub)
            if sub_score > 12:
                return self.get_substitute(user_input)
            else:
                # if zero shot score isn't high enough, just do a regular google search
                return self.get_url(user_input)

        # # if the user requests a subistitution, scrape information from the web and print it.
        # elif 's' in user_input[0]:
        #     return self.get_substitute(user_input[1:])

        # if none of the options above were identified as the task requested by the user, ask the user to type their request again   
        else:
            print("huh?")
            return self.default("confused")
    
    # This function prints the ingredient list and follows up appropriately
    # The only input to this function is a bool that identifies wether the function was called from the user typing 1 or by a natural language request
    def print_ingredients(self, first = False):
        # Printing the ingredient list
        print(f"{self.name}: Ok, here are the ingredients for '{self.recipe_name}'.\n")
        counter = 1
        for ing in self.ingredients:
            print(f"{counter}. {ing}")
            counter += 1
            print()

        #if the current step is at index 0 and the print_ingredients function was called by typing 1, ask the following
        if self.curr_step == 0 and first:
            print(f"{self.name}: Ok, would you like me to start going over the recipe steps (Yes / No)?\n")
        # If the current step is the last step, then go to the "done" state of the self.default function
        elif self.curr_step+2 > len(self.steps):
            return self.default("done")
        # If none of the above, than the user has seen the current step, so we need to ask if they want to see the next step
        else: 
            print(f"{self.name}: Ok, should I continue to step #{self.curr_step+2} of the recipe (Yes / No)?\n")
        
        r = input("User: ")
        print("\n")

        if r.lower().strip() == "no" or r.lower().strip() == "no.":
        # If the user does not want to see the recipe step suggested, go back to default state to ask the user what they want 
            return self.default()
        elif r.lower().strip() == "yes" or r.lower().strip() == "yes.":
            # if "first" is false and print_ingredients wasn't called by typing 1, then the user will want to see the next step
            if not first:
                self.curr_step += 1
            return self.print_step()
        else:
            return self.default("confused")
    
    # This function prints the current step and calls default
    def print_step(self):
        print(f"{self.name}: Here's step #{self.curr_step + 1}\n")
        print(f"{self.steps[self.curr_step]}\n")

        # Checks to see if we are at the end of the recipe steps to decide wether to call default with "done" or not
        if self.curr_step+2 > len(self.steps):
            return self.default("done")
        else:
            return self.default()
    
    # returns list of substitutes
    def get_substitute(self, query:str):
        query = re.sub("[.,;!]", "", query)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        url = "http://www.google.com/search?q=" + query + "&start=" + str((0))
        driver.get(url)
        query_html = BeautifulSoup(driver.page_source, 'html.parser')
        results = query_html.find_all('li', class_="TrT0Xe")
        substitutes = []
        if not results:
            results = query_html.find('div', class_="MjjYud")
            if results:
                results = results.find_all('span')
                for result in results:
                    if "." in result.text:
                        substitutes.append(result.text)
        else:
            for result in results:
                result = result.text.split('.')[0]
                substitutes.append(result)
        
        if substitutes:
            print(f"{self.name}: No worries. Here is a list of substitutes. \n")
            counter = 1
            for s in substitutes:
                print(f"{counter}. {s}")
                counter += 1
                print()
        else:
            return self.default("confused")

        # Checks to see if we are at the end of the recipe steps to decide wether to call default with "done" or not
        if self.curr_step+2 > len(self.steps):
            return self.default("done")
        else:
            return self.default()

    # FOR REQUIREMENTS 4 AND 5
    def get_url(self, query:str):
        query = re.sub("[.?,;!]", "", query)
        url = "https://www.google.com/search?q=" + query.replace(" ","+")

        print(f"{self.name}: No worries. I found a reference for you.\n{url}\n")

        # Checks to see if we are at the end of the recipe steps to decide wether to call default with "done" or not
        if self.curr_step+2 > len(self.steps):
            return self.default("done")
        else:
            return self.default()

    # This function takes the user input and labels to do zero shot classification, but it also takes a question to formulate
    # the input sequence to the zero shot pipeline in a "bot: [insert question] user: [inser user input]" format.
    # Optional threshold input that allows the function to return "confused" if the confidence score between the predicted label 
    # and the second predicted lable is below the threshold.
    # Otherwise returns the predicted label
    def zs_with_q(self, question, user_input, labels, threshold = None):
        zs_seq = f"Bot: {question} User: {user_input}"
        zs_dict = self.zero_shot_pipe(zs_seq, labels)
        label = zs_dict["labels"][0]

        if threshold:
            if zs_dict['scores'][0] - zs_dict['scores'][1] < threshold:
                label = "confused"
        
        return label
    
    # This function adds up the scores of each of the labels given by the zero shot classifier and returns the sum
    # it also adds a big bonus if the confidence score is really high (right now, instead of adding the confidence score, it adds 5)
    def zs_add_scores(self, user_input, labels):
        score_sum = 0
        for l in labels:
            score = self.zero_shot_pipe(user_input, l)["scores"][0]
            if score > 0.97: score = 5
            score_sum += score
            
        return score_sum


## STARTING A CONVERATION
def main():
    bot = RecipeBot()
    # here is the link I am using for testing:
    # https://tasty.co/recipe/fried-egg-pizza

if __name__ == '__main__':
    main()