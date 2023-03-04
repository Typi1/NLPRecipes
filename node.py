from typing import Optional

class recipeList:
    def __init__(self, recipe: list):
        self.recipe = recipe
        self.index = 0
    def get_all(self):
        return self.recipe
    def get_current(self):
        return self.recipe[self.index]
    def get_nth_prev(self, n: Optional[int] = None):
        if n:
            if self.index - n >= 0:
                self.index = self.index - n
                return self.recipe[self.index]
            else:
                print("Request is out of range!")
        else:
            if self.index - 1 >= 0:
                self.index = self.index - 1
                return self.recipe[self.index]
            else:
                print("Request is out of range!")
    def get_nth_next(self, n: Optional[int] = None):
        if n:
            if self.index + n <= len(self.recipe)-1:
                self.index = self.index + n
                return self.recipe[self.index]
            else:
                print("Request is out of range!")
        else:
            if self.index + 1 <= len(self.recipe)-1:
                self.index = self.index + 1
                return self.recipe[self.index]
            else:
                print("Request is out of range!")
    def get_nth(self, n: None):
        if n:
            if 0 <= n - 1 <= len(self.recipe)-1:
                self.index = n - 1
                return self.recipe[self.index]
    

# recipe = ["a", "b", "c", "d"]

# example = recipeList(recipe)
# # print(example.get_all())
# # print(example.get_current())
# print(example.get_nth_prev())
# print(example.get_nth_next(5))
# print(example.get_nth_next(3))
# # print(example.get_current())
# print(example.get_nth_prev())
# print(example.get_nth_prev(2))
# # print(example.get_current())
# print(example.get_nth(3))