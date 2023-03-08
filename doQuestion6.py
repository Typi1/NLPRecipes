import re
import stanza as st
import transformers as tra
import steps_parser
from typing import Optional


def getFirstTypeBroad(children:list, typ: str):
    res = None
    for branch in children:
        if typ in branch.label:
            return branch
        else:
            res = getFirstTypeBroad(branch.children, typ)
            if res != None and typ in res.label:
                return res
            
    return res

def getAllOfTypesNew(children:list, typs: list):
    res = []

    if len(children) == 1 and children[0].label == str(children[0]):
        return res
    
    # print("NN" in typs)

    for branch in children:
        if "NN" in typs and branch.label == "VP": 
            
            temp = getAllOfTypesNew(branch.children, typs)
            if temp != []:
                res += temp # res.append(temp)
            continue
        if any(branch.label == typ for typ in typs):
            if len(branch.children) == 1 and branch.children[0].label == str(branch.children[0]):
                res.append(branch.children[0].label)
            else:
                res.append(steps_parser.constituency_to_str(branch))
        # special case for collecting compound nouns 
        elif "NN" in typs and branch.label == "NP" and steps_parser.isComboNounPhrase(branch):
            res.append(steps_parser.constituency_to_str(branch))
        else:
            temp = getAllOfTypesNew(branch.children, typs)
            if temp != []:
                res += temp # res.append(temp)

    return res

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

    step_constii = depgram(step.original_text).sentences[0].constituency
    all_step_nouns = getAllOfTypesNew(step_constii.children, ["NN"])
    all_step_adj = getAllOfTypesNew(step_constii.children, ["JJ", "JJR", "JJS"])



    answer = ""

    # for quantity
    if max_score == quantity_score:
        # print("QUANTITY")
        ingredient_ranking = []
        for ingr in step.ingredients:
            pipe_res = pipe2(step.ingredients[ingr][0], object_of_question)
            ingredient_ranking.append((step.ingredients[ingr][0], pipe_res['scores'][0]))
        ingredient_ranking.sort(key=lambda x: x[1], reverse=True)
        max_ingredient_score = ingredient_ranking[0]
        # print(max_ingredient_score)
        is_quantity = re.search("\sof\s", max_ingredient_score[0]) != None or getFirstTypeBroad(depgram(max_ingredient_score[0]).sentences[0].constituency.children, "CD") != None#pipe2(max_ingredient_score[0], "number")['scores'][0] > 0.4 
        # print(is_quantity)

        if max_ingredient_score[1] < 0.4 or not is_quantity:
            ingredient_ranking = []
            if type(canon_ingredients[0]) != list:
                canon_ingredients = [canon_ingredients]
            # print(canon_ingredients)
            for canon_ingr in canon_ingredients[0]:
                test_docr = depgram(canon_ingr)
                deep = steps_parser.getDependency(test_docr.sentences[0].dependencies)[0]
                # for dd in deep:
                #     print(deep[dd])
                # print(deep[list(deep[0].deps.keys())[0]])
                temp = deep[list(deep[0].deps.keys())[0]]
                for dpk in list(temp.deps.keys()):
                    # print(temp.deps)
                    # print(dpk)
                    if temp.deps[dpk][2] == "conj":
                        # print(temp.deps[dpk][0])
                        temp = deep[temp.deps[dpk][0]]
                        break
                pipe_res = pipe2(canon_ingr, object_of_question)
                pipe_res2 = pipe2(temp.text, object_of_question)
                # print(canon_ingr)
                # print(pipe_res)
                ingredient_ranking.append((canon_ingr, max(pipe_res['scores'][0], pipe_res2['scores'][0] * 2)))
            ingredient_ranking.sort(key=lambda x: x[1], reverse=True)
            # print(ingredient_ranking)
            
            while re.search("\d", ingredient_ranking[0][0]) == None:
                ingredient_ranking = ingredient_ranking[1:]

            max_ingredient_score = ingredient_ranking[0]
        # print(max_ingredient_score)
        answer = max_ingredient_score[0]
    # for temperature
    elif max_score == temperature_score:
        # print("TEMPERATURE")
        detail_ranking = []
        for detail_id in step.details.keys():
            detail = step.details[detail_id]
            pipe_res = pipe2(detail[1], "temperature")
            detail_ranking.append((detail[1], pipe_res['scores'][0]))
        detail_ranking.sort(key=lambda x: x[1], reverse=True)
        # print(detail_ranking)
        if len(detail_ranking) > 0 and detail_ranking[0][1] > 0.6 and not detail_ranking[0][0].lower() == "temperature": 
            # print("??")
            answer = detail_ranking[0][0]
        elif len(detail_ranking) < 1 or detail_ranking[0][1] < 0.6:
            regex_minute_search = re.search("(\d+)\s+degrees", step.original_text)
            if regex_minute_search != None:
                answer = str(regex_minute_search.group(1)) + " degrees"
            
            if answer == "":
                temperature_noun_ranking = []
                for nn in all_step_nouns:
                    pipe_res = pipe2(nn, "temperature")
                    temperature_noun_ranking.append((nn, pipe_res['scores'][0]))
                temperature_noun_ranking.sort(key=lambda x: x[1], reverse=True)
                if len(temperature_noun_ranking) > 0 and temperature_noun_ranking[0][1] > 0.7:
                    # print("???")
                    answer = temperature_noun_ranking[0][0]
                
            if answer == "":
                temperature_adj_ranking = []
                for aa in all_step_adj:
                    pipe_res = pipe2(aa, "temperature")
                    temperature_adj_ranking.append((aa, pipe_res['scores'][0]))
                temperature_adj_ranking.sort(key=lambda x: x[1], reverse=True)
                if len(temperature_adj_ranking) > 0 and temperature_adj_ranking[0][1] > 0.7:
                    # print("????")
                    answer = temperature_adj_ranking[0][0]
        if answer == "" and "room temp" in step.original_text.lower():
            return "room temperature"
    # for time
    elif max_score == time_score:
        # print("TIME")
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