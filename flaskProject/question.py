class Question:
    def __init__(self, problem_title, problem_description, problem_tags, difficulty,
                 testcases, solution, tot_tokens):
        # self.problem_id = problem_id
        self.problem_title = problem_title
        self.problem_description = problem_description
        self.difficulty = difficulty
        self.tot_tokens = tot_tokens
        self.testcases = testcases
        self.solution = solution
        # self.hints = hints
        self.problem_tags = problem_tags
