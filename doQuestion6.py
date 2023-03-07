import re
import stanza as st
import transformers as tra
import steps_parser
from typing import Optional

# INPUTS:
# pipe2 is the zero-shot pipeline, 
# depgram is the stanza output (should be self.depgram), 
# canon_ingredients is just the list of ingredient strings (should be self.ingredients)
# step is the Step data structure from steps_parser. it should be indexable from self.steps_data NOTE that is a dictionary, so index by step number. indexes start at 1 for that
# OUTPUT:
# a string with either an answer string or a failure state answer
def goal6(pipe2, depgram, question: str, canon_ingredients:list,  step:steps_parser.Step, Q_type: Optional[str] = None):
    quantity_Q_list = ["How many do I need?",
                       "How much do I need?",
                       "What amount of this do I need?",
                       "Around how much of this ingredient do I need for this step?",
                       "Do I use a lot of this ingredient?",
                       "Do I use a little of this ingredient?",
                       "How many cups do I need?",
                       "What should I fill my measuring cup up to?",
                       "How much should I use?"] # add 6 more
    temperature_Q_list = ["How hot should it be?",
                          "How many degrees should it be set to?",
                          "How high do I set the oven?",
                          "What temperature should it be at?",
                          "What is the best temperature for this step?",
                          "How cold should it be?",
                          "How many degrees should I set it to?",
                          "How warm should I make it?",
                          "Should it be cool?"] # add 5 more
    time_Q_list = [ "How long should I do this?",
                    "How much time should this take?",
                    "How long do I wait?",
                    "How long will this take?",
                    "How many minutes do I do this?",
                    "How much time until I do this?",
                    "For how long?",
                    "What should I set my timer to?",
                    "When will this be done?",
                    "What should I check to see if it is done?",
                    "What should it look like when I'm done?",
                    "When is it done?",
                    "When should I stop?",
                    "How long should I microwave it for?"]
    
    parsed_input = depgram(question)
    (input_deps, _) = steps_parser.getDependency(parsed_input.sentences[0].dependencies)
    # for ii in input_deps:
    #     print(input_deps[ii])

    object_of_question = ""
    # print(list(input_deps[0].deps.keys())[0])
    # find the direct object of the root verb, it will be what the question is about
    for dd in input_deps[list(input_deps[0].deps.keys())[0]].deps:
        if input_deps[list(input_deps[0].deps.keys())[0]].deps[dd][2] == "obj" or input_deps[list(input_deps[0].deps.keys())[0]].deps[dd][2] == "nsubj":
            object_of_question = input_deps[dd].text
            break
    # print(object_of_question)
    if (object_of_question == "" or object_of_question == None) and "NN" in input_deps[list(input_deps[0].deps.keys())[0]].typ:
        object_of_question = input_deps[list(input_deps[0].deps.keys())[0]].text
    if object_of_question == "" or object_of_question == None:
        return None

    if Q_type == None:
        quantity_score = 0
        for q in quantity_Q_list:
            quantity_score += pipe2(question, q)['scores'][0]
        temperature_score = 0
        for q in temperature_Q_list:
            temperature_score += pipe2(question, q)['scores'][0]
        time_score = 0
        for q in time_Q_list:
            time_score += pipe2(question, q)['scores'][0]
    else:
        if Q_type.lower() == "quantity":
            quantity_score = 100
            temperature_score = 0
            time_score = 0
        elif Q_type.lower() == "temperature":
            quantity_score = 0
            temperature_score = 100
            time_score = 0
        else:
            quantity_score = 0
            temperature_score = 0
            time_score = 100

    # print(pipe2(question, candidate_labels=["how much", "what temperature", "for how long", "when"]))
    # print("quantity score: " + str(quantity_score))
    # print("temperature score: " + str(temperature_score))
    # print("time score: " + str(time_score))

    # print(step)
    max_score = max(quantity_score, temperature_score, time_score)
    if max_score < 1:
        return None

    answer = ""

    # for quantity
    if max_score == quantity_score:
        ingredient_ranking = []
        for ingr in step.ingredients:
            pipe_res = pipe2(step.ingredients[ingr][0], object_of_question)
            ingredient_ranking.append((step.ingredients[ingr][0], pipe_res['scores'][0]))
        ingredient_ranking.sort(key=lambda x: x[1], reverse=True)
        max_ingredient_score = ingredient_ranking[0]
        # print(max_ingredient_score)
        is_quantity = pipe2(max_ingredient_score[0], "amount")['scores'][0]
        # print(is_quantity)

        if max_ingredient_score[1] < 0.4 or is_quantity < 0.4:
            ingredient_ranking = []
            if type(canon_ingredients[0]) != list:
                canon_ingredients = [canon_ingredients]
            for canon_ingr in canon_ingredients[0]:
                pipe_res = pipe2(canon_ingr, object_of_question)
                # print(canon_ingr)
                # print(pipe_res)
                ingredient_ranking.append((canon_ingr, pipe_res['scores'][0]))
            ingredient_ranking.sort(key=lambda x: x[1], reverse=True)
            
            while re.search("\d", ingredient_ranking[0][0]) == None:
                ingredient_ranking = ingredient_ranking[1:]

            max_ingredient_score = ingredient_ranking[0]
        answer = max_ingredient_score[0]
    # for temperature
    elif max_score == temperature_score:
        detail_ranking = []
        for detail_id in step.details.keys():
            detail = step.details[detail_id]
            pipe_res = pipe2(detail[1], "temperature")
            detail_ranking.append((detail[1], pipe_res['scores'][0]))
        detail_ranking.sort(key=lambda x: x[1], reverse=True)
        # print(detail_ranking)
        if len(detail_ranking) > 0 and detail_ranking[0][1] > 0.6: answer = detail_ranking[0][0]
        elif len(detail_ranking) < 1 or detail_ranking[0][1] < 0.6:
            regex_minute_search = re.search("(\d+)\s+degrees", step.original_text)
            if regex_minute_search != None:
                answer = str(regex_minute_search.group(1)) + " degrees"
        
    # for time
    elif max_score == time_score:
        detail_ranking = []
        for detail_id in step.details.keys():
            detail = step.details[detail_id]
            # print(detail[1])
            pipe_res = pipe2(detail[1], "time")
            bonus = 0
            if "until" in detail[1]:
                bonus += 0.9
            if "minute" in detail[1]:
                bonus += 1
            if "second" in detail[1]:
                bonus += 1
            if detail[1] == "then":
                bonus -= 1
            detail_ranking.append((detail[1], pipe_res['scores'][0] + bonus))
        detail_ranking.sort(key=lambda x: x[1], reverse=True)
        # print(detail_ranking)
        if len(detail_ranking) > 0 and detail_ranking[0][1] > 0.6: answer = detail_ranking[0][0]
        elif len(detail_ranking) < 1 or detail_ranking[0][1] < 0.6:
            regex_minute_search = re.search("(\d+)\s+minute", step.original_text)
            if regex_minute_search != None:
                answer = str(regex_minute_search.group(1)) + " minutes"
        
    if answer == "":
        return None

    return "I believe this answers your question: " + answer + "\n"
    

# print(allsteps[10])
# print(allsteps2[1])
# print(goal6(pipe2, depgram, "How much salt?", 
#       #[['Strawberries:', '3 pint baskets fresh strawberries (about 6 cups)', '1/2 cup (100 g) white granulated sugar for the strawberries', 'Whipped Cream:', '1 cup (236 ml) heavy whipping cream', '2 teaspoons powdered sugar', '2 drops vanilla extract', 'Biscuits:', '3 1/4 cups (455g) all purpose flour, divided ( 3 cups and 1/4 cup)', '3 tablespoons sugar', '1 1/2 tablespoons baking powder', '3/4 teaspoon salt', '12 tablespoons (168g) unsalted butter, cut into small cubes', '1 cup (236 ml) milk', '1/4 (60 ml) cup heavy cream', '1 1/2 teaspoons vanilla extract']], 
#       #['all-purpose flour, for dusting', '12 oz prepared pizza dough', '2 tablespoons olive oil, divided', '6 large eggs, separated', '½ cup prepared pizza sauce', '½ cup frozen spinach, thawed and squeezed dry', '½ cup shredded whole-milk mozzarella cheese', '½ teaspoon dried oregano', '¼ teaspoon crushed red pepper flake', '¼ teaspoon kosher salt', '¼ teaspoon ground black pepper', '2 tablespoons grated parmesan cheese']
#       ['Kosher salt', '12 ounces linguine', '1 1/4 pounds large shrimp, peeled and deveined', '1/3 cup extra-virgin olive oil\xa0', '5 cloves garlic, minced', '1/4 to 1/2 teaspoon red pepper flakes', '1/3 cup dry white wine', 'Juice of 1/2 lemon, plus wedges for serving', '4 tablespoons unsalted butter, cut into pieces', '1/4 cup finely chopped fresh parsley']
#       ,
#       allsteps2[4]))

# print(pipe2("hello", "greeting"))