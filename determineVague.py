def getFirstTypeBroad(children:list, typ: str):
    res = None
    for branch in children:
        # print(branch.label)
        if typ in branch.label:
            return branch
        else:
            res = getFirstTypeBroad(branch.children, typ)
            if res != None and typ in res.label:
                return res
            
    return res

def is3(depgram, text:str):
    if text == "":
        return False
    test_doc = depgram(text)
    consti = test_doc.sentences[0].constituency
    # print(consti)
    return getFirstTypeBroad(consti.children, "NN") == None