# MealMaster

By:
    Gustavo Carvalho
    Sean Lee
    Ethan Kim

## 1) Description
MealMaster is a simple conversational assistant that helps you while cooking a recipe. Here are the following ways MealMaster can help you:

1. Can print out the ingredient list when asked
2. Can read the recipe steps (can respond to commands such as "Show me the next step", "Show me the previous step", and "Take me to the *insert number* th step")
3. Can answer "how to" questions ("How do I *insert specific technique*?")
4. Can answer vague "how to" questions ("How do I do that?")
5. Can answer simple "what is" questions ("What is a *insert tool being mentioned*?")
6. Can answer questions about the parameters of the current step ("How much of *insert ingredient* do I need?", "What temperature?", "How long do I *insert specific technique*?", "When is it done?")
7. Can answer ingredient substitution questions ("What can I substitute for *insert ingredient*?")

## 2) How it's able to do what it does

The way MealMaster works is through:
1. Clever conversational design
2. A system of zero-shot classification that determines what the user input means
3. Separate functions that do each of the tasks detailed in Section 1 (Description Section)

### Clever conversational design
Firstly, we implemented a strict conversational flow to induce our users to only input text that Mealmaster can handle. The beggining of the conversation starts with MealMaster prompting the user to either type '1' to see the ingredients list or '2' to recipe steps. After this initial interaction, the bot will fall into the following loop: default() -> interpret() -> a task function -> default(). This loop helps frame the conversation so that the user continually types in commands for MealMaster, which is what the bot was built to handle.

Now 

Default():
Essentially, what default() does is that it decides to continue the conversation by calling interpret() or to end the conversation, while aslo dealing with some edge cases. If default() decided to continue the conversation, it will print a message of the sorts "What else would you like me to do?" and then call interpret(). If default() decides to end the conversation, then it will first ask if the user has any last questions before ending the conversation for good.

The two edge cases default handles are the following: (1) the bot can't figure out what the user wants and (2) the user typed nothing. In both cases, default() prints a message asking the user to repeat themselves before calling interpret() again.

Interpret():
The interpret() function is the most important function of the bot. It recieves as input whatever the user typed and calls the correct function to respond. In a high level, here is what interpret() does:
1. From the user input, interpret() determines what task the user wants MealMaster to do;
2. Given the task, interpret() checks if the task is possible (ex: You can't go to the 100th step if the recipe only has 20 steps)
3. If the task is possible, interpret() changes the corresponding class variables needed to complete the task (for instance, if the user asks to go to the next step, a class variable that points to the current step has to change) and then it calls the function that does the requested task (in the example I gave, it would call print_step(), which prints the current step the aformentioned class variable is pointing to).
4. If the task is not possible, then print an appropriate message and call default()

Additionally, if interpret() can't figure out what task the user wants to be done (or if the user types nothing), it will call default() with the needed input to trigger a "confused script" (have the bot ask "Could you please repeat?")

Task Functions:
Task functions simply do one of the tasks detailed in Section 1 and then call the default() function. These functions do various different things to accomplish their respective task. From simply printing messages, to doing webscraping, to using Stanza (a python NLP package) to parse the steps and ingredients for information.

### Zero-Shot Classification
Zero-shot classification is used for interpret() to map user inputs to the task functions. By using a Large Language Model (LLM) from HuggingFace and a given label, we are able to calculate a "confidence score" of how likely the LLM thinks the label describes the user input. We use a set of labels for each task and determine what task the user input is requesting by adding up the confidence scores and then picking the highest sum. Calculating the different confidence scores is what makes MealMaster take a bit to respond to each user input, however, we believe this is worth it since (in theory) this is more robust than hard coded heuristics.
Lastly, if all of the confidence score sums are low, that is when interpret() calls default() to trigger the "confused script".

** in practice, interpret() actually uses a combination of zero-shot and hard coded heuristics to determine what task the user is requesting, however, zero-shot definetly does the bulk of the work. Furthermore, setting up the zero-shot system was far from trivial and required a lot of testing to optimize the label lists, determine the method of summing up the confidence scores, and choosing the lower bound which determines wether the "confused script" is triggered.


## 3) Which Recipes MealMaster Can Use

You can give MealMaster the urls from any of the following recipe websites:
1. allrecipes.com
2. simplyrecipes.com
3. foodnetwork.com
4. tasty.co

Any other recipe webiste is not guaranteed to work.

## 3) Installation
1. Download the github repo
2. Install all packages by running $ pip install -r requirements. txt
3. Run the file MealMaster.py to start the bot! 

REQUIRES Python 3.10 OR LATER TO RUN

Github repository: https://github.com/Typi1/NLPRecipes
