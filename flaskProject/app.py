import os
import openai
import requests
from pymongo import MongoClient
from flask import Flask, render_template, redirect, request
from question import Question

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017")

db = client["knowledge_pool"]
collection = db['questions_generated']

openai.api_key = "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"

messages = [{
    "role": "system",
    "content": "You are a problem setter who has to make dsa problems"
               " like there are in leetcode."
},
]


# @app.route("/", methods=("GET", "POST"))
# def home():
#     return render_template()


@app.route('/', methods=['GET', 'POST'])
def handle_form():
    if request.method == "POST":
        n: int = 1
        action = request.form['action']
        subtopic = request.form["subtopic"]
        difficulty = request.form["difficulty"]
        number = request.form["number"]
        # solution_wanted = request.form["solution_wanted"]

        if action == 'generate':
            # generating question
            questions = []
            while n <= int(number):
                ques = new_gen(subtopic, difficulty)
                questions.append(ques)
                n += 1

        elif action == 'retrieve':
            questions = pre_gen(subtopic, difficulty, number)
        return render_template('question_display.html', question=questions[0])

    else:
        return render_template("index.html")


@app.route('/questions/<problem_id>')
def question_display(problem_id):
    document = collection.find_one({'_id': problem_id})
    question = Question(document['problem_title'],
                        document['problem_description'],
                        document['problem_tags'],
                        document['difficulty'],
                        document['testcases'],
                        document['solution'],
                        document['problem_id'],
                        document['tot_tokens']
                        )
    print(document['problem_title']+
            document['problem_description']+
            document['problem_tags']+
            document['difficulty']+
            document['testcases']+
            document['solution']+
            document['problem_id']+
            document['tot_tokens'])
    return render_template('question_display.html', question=question)


def new_gen(subtopic, difficulty):
    # prompt to generate question of given difficulty and on given subtopic
    question_prompt: str = f"Generate a unique DSA problem (C++) based on the subtopics {subtopic} " \
                           f"with a level of difficulty of {difficulty} with 10 being max difficluty.\
                            Do not provide the solution at all.\
                            If it is complex to understand give examples and necessary hints for understanding.\
                            Generate testcases for examples and testing of code.\
                            Keep in mind that the testcases should include basic cases as well \
                            as edge cases for time complexity checking and constraint checking.\n"
    messages.append(
        {"role": "user", "content": question_prompt},
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )

    # tokens used in API Call
    total_ques_tokens = chat.usage.get('total_tokens')

    # storing question
    question = chat.choices[0].message.content
    # print(f"ChatGPT: {question}")

    # tags generation
    tags_prompt = f"Give all of the concepts used in the problem like " \
                  f"arrays, graphs, bfs, dfs, trees etc."
    messages.append(
        {"role": "user", "content": tags_prompt},
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )
    tags = chat.choices[0].message.content
    tags = tags.replace(".", "")
    tags = tags.strip()
    tags = (tags.split(','))
    problem_tags = tuple(element.strip() for element in tags)
    # tokens used in API Call
    total_tags_tokens = chat.usage.get('total_tokens')

    # testcase generation
    testcases_prompt: str = f"Now generate testcases for examples and testing of code. " \
                            f"Keep in mind that the testcases should include " \
                            f"basic cases as well as edge cases for time complexity checking and constraint checking."
    # if testcases_prompt:
    messages.append(
        {"role": "user", "content": testcases_prompt}
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )

    # tokens used in API Call
    total_testcase_tokens = chat.usage.get('total_tokens')

    # storing testcases
    testcases = chat.choices[0].message.content

    # # hint generation
    # hints_prompt: str = f"Now generate hints for a person solving the {question}. " \
    #             f"Keep in mind that hints should be gradual, and leading to the solution " \
    #             f"and not giving away the solution entirely and should explain the logic in steps. " \
    #             f"Hints can be anywhere between 1 to 4."
    # messages.append(
    #     {"role": "user", "content": hints_prompt}
    # )
    # chat = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo", messages=messages
    # )
    #
    # # tokens used in API Call
    # total_hint_tokens = chat.usage.get('total_tokens')
    #
    # # storing hints
    # hints = chat.choices[0].message.content

    # solution generation
    messages.append({"role": "assistant", "content": question})
    solution_prompt: str = "Now provide the complete c++ code of the question " + question
    messages.append(
        {"role": "user", "content": solution_prompt},
    )
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )

    # token used in solution generation
    total_ans_tokens = chat.usage.get('total_tokens')

    # storing solution of the question
    solution = chat.choices[0].message.content

    tot_tokens = total_ans_tokens \
                 + total_testcase_tokens \
                 + total_ques_tokens \
                 + total_tags_tokens
    problem_title = "A problem on DSA"
    # object1 = collection.insert_one({
    #     'problem_title': problem_title,
    #     'problem_description': question,
    #     'problem_tags': problem_tags,
    #     'difficulty': difficulty,
    #     'testcases': testcases,
    #     'solution': solution,
    #     'tot_tokens': tot_tokens}
    # )
    # print(question)
    # print(problem_tags)
    # print(testcases)
    # print(solution)
    # print(tot_tokens)
    # problem_id = object1.inserted_id
    question_obj = Question(problem_title, question, problem_tags,
                            difficulty, testcases, solution,
                            tot_tokens)
    return question_obj


def pre_gen(subtopic, difficulty, number):
    tags1 = tuple(tag.strip() for tag in subtopic.split(','))
    list1 = list(tags1)
    questions_list = []
    document_found = False
    if difficulty == "":
        resultx = collection.find({
            "problem_tags": {"$all": list1}}).\
            sort(["difficulty"]).\
            limit(int(number))
        for document in resultx:
            document_found = True
            question_obj = Question(document['problem_title'],
                                    document['problem_description'],
                                    document['problem_tags'],
                                    document['difficulty'],
                                    document['testcases'],
                                    # document['hints'],
                                    document['solution'],
                                    document['problem_id'],
                                    document['tot_tokens']
                                    )
            questions_list.append(question_obj)
        if not document_found:
            questions_list.append()
    else:
        resultx = collection.find({
            "problem_tags": {"$all": list1},
            "difficulty": difficulty
        }).limit(int(number))
        for document in resultx:
            document_found = True
            question_obj = Question(document['problem_title'],
                                    document['question'],
                                    document['problem_tags'],
                                    document['difficulty'],
                                    document['testcases'],
                                    # document['hints'],
                                    document['solution'],
                                    document['problem_id'],
                                    document['tot_tokens']
                                    )
            questions_list.append(question_obj)
        if not document_found:
            questions_list.append()
    return questions_list


if __name__ == '__main__':
    app.run(debug=True)

# temp = "Out of the following tags, which ones are used in the question. " \
#                   "Tags: expression parsing,fft,two_pointers,binary_search,dsu,strings,number_theory," \
#                   "data_structures,hashing,shortest_paths,matrices,string_suffix_structures," \
#                   "graph_matchings,dp,dfs_and_similar,meet-in-the-middle,games,schedules,constructive_algorithms," \
#                   "greedy,bitmasks,divide_and_conquer,flows,geometry,math,sortings,ternary_search,combinatorics," \
#                   "brute_force,implementation,2-sat,trees,probabilities,graphs,chinese_remainder_theorem. " \
#                   "Here's how you should respond: Do not write any introductory line. " \
#                   "Just write the tags as mentioned in the list in one line. " \
#                   "If there are multiple words in a tag use underscore. " \
#                   "Separate them using commas. Be very careful that there is no space after a comma. " \
#                   "No full stop."