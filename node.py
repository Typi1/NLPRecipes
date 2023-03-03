class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class recipeList:
    def __init__(self, recipe):
        self.head = Node(recipe[0])
        self.curr = self.head
        self.recipe = self.head
        for i in range(1, len(recipe)):
            self.recipe.next = Node(recipe[i])
            self.recipe.next.prev = self.recipe
            self.recipe = self.recipe.next
    def get_prev(self):
        if self.curr.prev:
            self.curr = self.curr.prev
            print(self.curr.data)
        else:
            print("This is the first instruction in the recipe!")
    def get_next(self):
        if self.curr.next:
            self.curr = self.curr.next
            print(self.curr.data)
        else:
            print("This is the last instruction in the recipe!")
    

recipe = ["a", "b", "c"]

example = recipeList(recipe)
print("Current node: " + example.curr.data)
example.get_prev()
example.get_next()
example.get_next()
example.get_prev()
example.get_next()
example.get_next()