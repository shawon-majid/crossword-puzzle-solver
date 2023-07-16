from collections import deque
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        for variable in self.crossword.variables:
            currentLength = variable.length
            words = list(self.domains[variable])

            for word in words:
                if len(word) != currentLength:
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        revised = False

        domainOfX = list(self.domains[x])
        domainOfY = list(self.domains[y])

        for value in domainOfX:
            # if I use current value in x, do I have options in Y? If no option in Y, then I can remove value
            if self.crossword.overlaps[x, y] == None:
                continue

            i, j = self.crossword.overlaps[x, y]

            # if value[i] y r domain or kono value er loge match na kore
            noOption = True
            for value2 in domainOfY:
                if value[i] == value2[j]:
                    noOption = False
                    break
            if noOption:
                self.domains[x].remove(value)
                revised = True
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        if arcs == None:  # get all the arcs
            arcs = deque()
            for variable in self.crossword.variables:
                for neighbor in self.crossword.neighbors(variable):
                    arcs.append((variable, neighbor))

        while len(arcs) > 0:
            x, y = arcs.popleft()
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        arcs.append((z, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if variable not in assignment.keys():
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        # every value is distinct
        # every value is correct lenght
        # no conflict between neighboring values

        unique = self.isUnique(assignment)
        correctLength = self.isCorrectLength(assignment)
        constraints = self.checkConstraints(assignment)

        if unique and correctLength and constraints:
            return True

        return False

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        # var = Variable(var) # delete it later
        # assignment = dict() # delete it later

        domainList = list(self.domains[var])

        domainListWithR = []

        for value in domainList:

            cntOfRuleOut = 0
            for neighbor in self.crossword.neighbors(var):

                if neighbor in assignment.keys():
                    continue

                if (self.crossword.overlaps[var, neighbor] == None):
                    continue

                i, j = self.crossword.overlaps[var, neighbor]

                for value2 in self.domains[neighbor]:
                    if value[i] != value2[j]:
                        cntOfRuleOut += 1

            domainListWithR.append((value, cntOfRuleOut))

        orderedDomainList = sorted(domainListWithR, key=lambda x: x[1])

        return [x[0] for x in orderedDomainList]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        # assignment = dict() # delete it later

        variableList = []

        for variable in self.crossword.variables:
            if variable not in assignment.keys():
                variableList.append((variable, len(self.domains[variable]), len(
                    self.crossword.neighbors(variable))))

        # least domain
        # most neighbors

        minSizeOfDomain = None
        maxSizeOfNeighbour = None
        answer = None

        for v, d, n in variableList:
            if minSizeOfDomain == None or d <= minSizeOfDomain:

                if minSizeOfDomain == None:
                    answer = v
                    minSizeOfDomain = d
                    maxSizeOfNeighbour = n

                elif d < minSizeOfDomain:
                    answer = v
                    minSizeOfDomain = d
                    maxSizeOfNeighbour = n
                if d == minSizeOfDomain:
                    if n > maxSizeOfNeighbour:
                        answer = v
                        minSizeOfDomain = d
                        maxSizeOfNeighbour = n

        return answer

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):

            return assignment

        var = self.select_unassigned_variable(assignment)

        values = self.order_domain_values(var, assignment)

        for value in values:
            newAssignment = assignment.copy()
            newAssignment[var] = value
            self.ac3();
            if self.consistent(newAssignment):
                result = self.backtrack(newAssignment)
                if result != None:
                    return result

        return None

    # The following 3 functions are added later

    def isUnique(self, assignment):
        values = set()

        for key in assignment.keys():
            values.add(assignment[key])

        return len(values) == len(assignment)

    def isCorrectLength(self, assignment):
        # assignment = dict() # need to delete it later

        correctLength = True

        for variable in assignment.keys():
            # variable = Variable(variable) # need to delete

            if variable.length != len(assignment[variable]):
                correctLength = False
                break

        return correctLength

    def checkConstraints(self, assignment):
        # assignment = dict() # need to delete it later

        constraintSatisfied = True

        for variable in assignment.keys():
            # variable = Variable(variable) # need to delete

            for neighbor in self.crossword.neighbors(variable):

                if neighbor in assignment.keys():

                    if self.crossword.overlaps[variable, neighbor] == None:
                        continue

                    i, j = self.crossword.overlaps[variable, neighbor]

                    if assignment[variable][i] != assignment[neighbor][j]:
                        constraintSatisfied = False
                        break
            if constraintSatisfied == False:
                break

        return constraintSatisfied


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = {}
    assignment = creator.solve()

    # print(assignment)

    # Print result
    if assignment is None:
        print("No solution.")
        creator.save(assignment, output)
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
