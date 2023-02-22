import stanza as st
import numpy as np
import re as reg
from typing import Optional
import transformers as tra
from enum import Enum

pipe = tra.pipeline(model="facebook/bart-large-mnli")

# print(pipe("bowl", candidate_labels=["food", "cooking utensil", "appliance", "container"]))

class DetailType(Enum):
    TIME = 0 # an amount of time (or "until...")
    TEMPERATURE = 1 # a temperature
    LOCATION = 2 # where to perform the step (like in a bowl, over a colinder)
    PREP_MANNER = 3 # evenly, 
    MACHINE_SETTING = 4 # non-temperature machine setting (like blender speed)
    OPTIONAL = 5 # if the instruction is optional or at user discretion. usually can be indicated by "IF"
    
    MISC = 10 # if it doesn't fit significantly into any of the other categories. observe this to see if there are any commonalities to make categories

class protoStep:
    def __init__(   self,
                    id: int = 0, # the number of the step
                    action: str = "", # the root action of the step
                    nouns: dict = None, # the nouns involved in the steps with name as key, 
                    # and a list with its type [0] and then another list of associated strings [1] as values
                    original_text: str = "" # the original text
                    ):
        self.id = id
        self.action = action
        self.nouns = {}
        if nouns != None:
            self.nouns = nouns
        self.original_text = original_text

    

    def __str__(self):
        outputStr = ""
        outputStr = outputStr +  "id: " + str(self.id)
        outputStr = outputStr + "\nOriginal text: " + str(self.original_text)
        outputStr = outputStr + "\n\tRoot action: " + str(self.action)
        outputStr = outputStr + "\n\tNouns: " + str(self.nouns)
        return outputStr

# note when going over ingredients, if there is a verb associated with it (like chopped leeks), make it a step if not already (chop leeks)

class Step:
    def __init__(   self, 
                    id: int = 0, # the number of the step
                    action: str = "", # the root verb of the step
                    ingredients: dict = None, # the ingredients required as keys (num/amount [count/mass] and list of qualifiers [adjs] as value)
                        # could also use some ingredient ID instead of using a list of qualifiers on the ingredient [the class referred to by the ID]
                    tools: dict = None, # the tools and/or appliances and/or pots/pans/bowls required
                    details: dict = None, # adverbs and descriptors. key is a numerical ID. value is DetailType enum and substring
                    original_text: str = ""): 
        self.action = action
        self.ingredients = {}
        if ingredients != None:
            self.ingredients = ingredients
        self.tools = {}
        if tools != None:
            self.tools = tools
        self.details = {}
        if details != None:
            self.details = details
        self.id = id 
        self.original_text = original_text



    def __str__(self):
        outputStr = ""
        outputStr = outputStr +  "id: " + str(self.id)
        outputStr = outputStr + "\nOriginal text: " + str(self.original_text)
        outputStr = outputStr + "\n\tRoot action: " + str(self.action)
        outputStr = outputStr + "\n\tIngredients: " + str(self.ingredients)
        outputStr = outputStr + "\n\tTools: " + str(self.tools)
        outputStr = outputStr + "\n\tDetails: " + str(self.details)
        return outputStr
    
def getNounType(text:str, seen: dict):
    res = ""
    if text in seen:
            res = seen[text]
    else:
        res = pipe(text, candidate_labels=["ingredient","appliance","cooking utensil","time","container","amount"])
        seen[text] = res

    # print(res)
    return (res['labels'][0], seen)

def getPrepositionPhrases(text:str):
    # do a breadth-first search through the consistuency tree to retrieve the prepositional phrase
    # also identify whether it is referring to a location on a food item or an appliance (cookware)
    pass

# test_phrase = "Blend the sweet strawberry cream in the blender with cinnamon."
# test_phrase = "After preparing 20 pounds of batter, insert it into a lovely pan."
test_phrase = "In a medium bowl, whisk the confectioners' sugar with the lemon zest, lemon juice, butter and salt until smooth. Drizzle the glaze overthe top of the cake, letting it drip down the sides. Let stand for 20 minutes until the glaze is set. Cut the cake into wedges and serve."

st.download('en')
depgram = st.Pipeline('en')#, processors='tokenize,mwt,pos,lemma,depparse,ner')
test_doc = depgram(test_phrase)

# print(test_doc)
# print(test_doc.entities)
steps = {}
protos = {}
curr_id = 1
pipe_seen = {}

for sent in test_doc.sentences:
    consti = sent.constituency
    print(consti)
    print(consti.label) 
    print(consti.children) # do some tree traversal to find preposition phrases and add them to details(?) Probably BFS
    print(consti.children[0])
    print(len(consti.children))

    print(sent.text)
    root = ""
    ingredients = {}
    tools = {}
    details = {}

    noun_groupings = {} # noun as key, subordinate adjectives, nouns, and numbers as values

    for wrd in sent.words:
        
        noun_type = None
        head_word = None
        if wrd.head != None: head_word = sent.words[wrd.head-1]

        if wrd.deprel == "punct":
            continue
        
        print(wrd.text, wrd.lemma)
        print("\t" + wrd.pos)
        print("\thead: " + str(wrd.head-1) + " " + head_word.text) # note ID is 1-indexed, NOT 0-indexed
        print("\t" + wrd.deprel)
        if wrd.feats != None: 
            print("\t" + wrd.feats)

        if wrd.deprel == "root":
            root = wrd.text
            continue

        if wrd.pos == "NOUN":
            # if this noun is new, add it to the dictionary fresh
            if not wrd.text in noun_groupings.keys():
                (noun_type, pipe_seen) = getNounType(wrd.text, pipe_seen)

                noun_groupings[wrd.text] = [noun_type, []]


            # if this noun has a superordinate noun, check if that is in the groupings dict (add it if not),
            # and add the current noun to its list of qualifiers
            if head_word.pos == "NOUN":
                sub_noun_type = pipe(wrd.text, candidate_labels=["number", "consituent"])['labels'][0]
                # note that some values in this can be keys to a larger description of them
                # EX:   {'pounds': ['amount', [('10', 'number'), ('CREAM', 'consituent')]], 
                #       'CREAM': ['ingredient', [('strawberry', 'consituent')]]}
                if not head_word.text in noun_groupings.keys():
                    (temp_head_results, pipe_seen) = getNounType(head_word.text, pipe_seen)
                    noun_groupings[head_word.text] = [temp_head_results, []]
                
                noun_groupings[head_word.text][1].append((sub_noun_type, wrd.text))
                
        # if wrd.pos == "ADP" or wrd.pos == "DET" or wrd.pos == "NUM":
        if head_word.pos == "NOUN" and wrd.pos != "VERB":

            # if the current word is an adjective, 
            if wrd.pos == "ADJ":
                # if the current head noun isn't in the groupings dict, add it
                if not head_word.text in noun_groupings.keys():
                    (temp_head_results, pipe_seen) = getNounType(head_word.text, pipe_seen)
                    noun_groupings[head_word.text] = [temp_head_results, []]
                # get a type for the adjective
                sub_adj_type = pipe(wrd.text, candidate_labels=["preparation manner", "compliment", "color", "texture", "temperature", "viscosity", "taste", "size"])['labels'][0]
                # add the adjective to the list of qualifiers associated with the head noun
                noun_groupings[head_word.text][1].append((sub_adj_type,wrd.text))
            elif wrd.pos == "NUM":
                if not head_word.text in noun_groupings.keys():
                    (temp_head_results, pipe_seen) = getNounType(head_word.text, pipe_seen)
                    noun_groupings[head_word.text] = [temp_head_results, []]
                noun_groupings[head_word.text][1].append(("number",wrd.text))

        #     if head_word.text in noun_to_ADP.keys():
        #         if wrd.text in noun_to_ADP.keys():
        #             noun_to_ADP[head_word.text][0] = noun_to_ADP[head_word.text][0] + " " + noun_to_ADP[wrd.text][0] + " " + wrd.text
        #         else:
        #             noun_to_ADP[head_word.text][0] = noun_to_ADP[head_word.text][0] + " " + wrd.text
        #     else:
        #         if wrd.text in noun_to_ADP.keys():
        #             noun_to_ADP[head_word.text] = [noun_to_ADP[wrd.text][0] + " " + wrd.text, ""]
        #         else:
        #             noun_to_ADP[head_word.text] = [wrd.text, ""]
        # if wrd.text in noun_to_ADP.keys():
        #     noun_to_ADP[wrd.text][1] = noun_to_ADP[wrd.text][0] + " " + wrd.text
        #     noun_to_ADP[wrd.text][0] = noun_to_ADP[wrd.text][0] + " " + wrd.text

        
    # for x in noun_to_ADP.keys():
    #     temp_phrase_pipe = pipe(noun_to_ADP[x][1], candidate_labels=["temperature","container", "quantity", "ingredient", "time","cooking appliance", "location", "cooking utensil","wrapping", "cutlery","meal"])
    #     # print(temp_phrase_pipe)
    #     noun_to_ADP[x] = (temp_phrase_pipe['labels'][0], noun_to_ADP[x][0])
    
    # print(noun_to_qualifiers)
    # print(noun_to_ADP)
    
    # for x in noun_to_ADP.keys():
    #     if noun_to_ADP[x][0] == "ingredient" or noun_to_ADP[x][0] == "meal":
    #         ingredients[x] = noun_to_ADP[x][1]
    #     elif noun_to_ADP[x][0] == "container" or  noun_to_ADP[x][0] == "cooking appliance" or noun_to_ADP[x][0] == "cooking utensil"  or noun_to_ADP[x][0] == "food packaging"  or noun_to_ADP[x][0] == "wrapping" or noun_to_ADP[x][0] == "cutlery" or noun_to_ADP[x][0] == "location":
    #         tools[x] = noun_to_ADP[x][1]
    #     else:
    #         details[x] = noun_to_ADP[x][1] 

    # steps[curr_id] = Step(curr_id, root, ingredients, tools, details, sent.text)
    print(noun_groupings)

    protos[curr_id] = protoStep(curr_id, root, noun_groupings, sent.text)

    curr_id += 1

# for x in steps.keys():
#     print(steps[x])


for x in protos.keys():
    print(protos[x])


# (ROOT (S (VP (VB Divide) (NP (DT the) (NN batter)) (PP (IN between) (NP (DT the) (VBN prepared) (NNS pans)))) (. .)))







