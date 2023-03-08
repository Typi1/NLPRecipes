# import stanza as st
# import transformers as tra
# import re
import steps_parser 



# returns the id, text, and type of the head word of the given dependency dict (in depNode form)
def getHeadWord(input_deps:dict):
    return input_deps[list(input_deps[0].deps.keys())[0]]

def doQ3(pipe2, depgram, user_input:str, step:steps_parser.Step):
    # action we want info on
    base_action = None
    # get the action of the user input. This should be a how-type question. defaults to the root action
    parsed_input = depgram(user_input)
    dependency = steps_parser.getDependency(parsed_input.sentences[0].dependencies)[0]
    # print(dependency)
    user_head = getHeadWord(dependency)
    # print(user_head)
    if "VB" in user_head.typ:
        base_action = user_head.text
    else:
        base_action = step.root_action

    if base_action == None:
        return "Sorry, could you rephrase that?"

    # look through the actions of the step and get a similarity ranking of the action verb while adding the phrase to a list
    viable_action_phrases = []
    for action_id in step.actions:
        
        action = step.actions[action_id]
        # print(action)
        # print(base_action)
        action_score = pipe2(base_action, candidate_labels=action[0])['scores'][0]

        viable_action_phrases.append((action_score, action[1]))

    # now if viable_action_phrases is empty, then we can't do anything so error
    if len(viable_action_phrases) == 0:
        return "Sorry, could you rephrase that?"
    
    # if we got some action phrases, sort them by most fitting based on the zero shot
    viable_action_phrases.sort(key=lambda x: x[0], reverse=True)

    # print(viable_action_phrases[0][1])

    return viable_action_phrases[0][1]