import os
import ast
import json
import openai
from helper_functions import llm

# Load the JSON file
filepath = './data/courses-full.json'
with open(filepath, 'r', encoding='utf-8') as file:
    dict_of_courses = json.load(file)

# Build the category -> course names map from the data so names always match
category_n_course_name = {}
for _name, _course in dict_of_courses.items():
    category_n_course_name.setdefault(_course['category'], []).append(_name)


def identify_category_and_courses(user_message):
    delimiter = "####"

    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be enclosed in
    the pair of {delimiter}.

    Decide if the query is relevant to any specific courses
    in the Python dictionary below, which each key is a `category`
    and the value is a list of `course_name`.

    If there are any relevant course(s) found, output the pair(s) of a) `course_name` the relevant courses and b) the associated `category` into a
    list of dictionary object, where each item in the list is a relevant course
    and each course is a dictionary that contains two keys:
    1) category
    2) course_name

    {category_n_course_name}

    If are no relevant courses are found, output an empty list.

    Ensure your response contains only the list of dictionary objects or an empty list, \
    without any enclosing tags or delimiters.
    """

    messages =  [
        {'role':'system',
         'content': system_message},
        {'role':'user',
         'content': f"{delimiter}{user_message}{delimiter}"},
    ]
    category_and_product_response_str = llm.get_completion_by_messages(messages)
    try:
        return json.loads(category_and_product_response_str)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(category_and_product_response_str)
        except (ValueError, SyntaxError):
            return []
    

def get_course_details(list_of_relevant_category_n_course: list[dict]):
    course_names_list = []
    for x in list_of_relevant_category_n_course:
        course_names_list.append(x.get('course_name')) # x["course_name"]

    list_of_course_details = []
    for course_name in course_names_list:
        details = dict_of_courses.get(course_name)
        if details:
            list_of_course_details.append(details)
    return list_of_course_details


def generate_response_based_on_course_details(user_message, product_details):
    delimiter = "####"

    system_message = f"""
    You are a warm, knowledgeable course advisor for an online learning
    platform. Your goal is to help each customer feel understood and confident
    in choosing the right course. The customer query is delimited by a pair
    of {delimiter}.

    Course information (your ONLY source of facts):
    {product_details}

    Follow these steps:

    Step 1:{delimiter} Work out what the customer really wants (course details,
    price, comparison, suitability for their level or goals).

    Step 2:{delimiter} Check which facts in the course information answer it.
    If the course information is empty or does not cover the question, do not
    guess or invent anything.

    Step 3:{delimiter} Write the reply to the customer:
    - Open with a friendly, personal sentence that acknowledges their goal.
    - Use only facts from the course information: name, provider, course code,
      duration, rating, price, skills covered and what the course is about.
      Never invent prices, dates, discounts or outcomes.
    - Explain how the course helps with THEIR goal, not just a list of facts.
    - If several courses are relevant, compare them briefly (a short bullet
      list or table) and recommend one, saying why.
    - If no course matches, say so kindly, ask a clarifying question about
      their interests or experience, and suggest they browse the course list.
    - Keep it clear and scannable (short paragraphs or bullets, under ~200
      words) and end with a helpful follow-up question or next step.

    Use the following format:
    Step 1:{delimiter} <step 1 reasoning>
    Step 2:{delimiter} <step 2 reasoning>
    Step 3:{delimiter} <reply to customer>

    Make sure to include {delimiter} to separate every step.
    """

    messages =  [
        {'role':'system',
         'content': system_message},
        {'role':'user',
         'content': f"{delimiter}{user_message}{delimiter}"},
    ]

    response_to_customer = llm.get_completion_by_messages(messages)
    response_to_customer = response_to_customer.split(delimiter)[-1].strip()
    return response_to_customer


def process_user_message(user_input):
    delimiter = "```"

    # Process 1: If Courses are found, look them up
    category_n_course_name = identify_category_and_courses(user_input)
    print("category_n_course_name : ", category_n_course_name)

    # Process 2: Get the Course Details
    course_details = get_course_details(category_n_course_name)

    # Process 3: Generate Response based on Course Details
    reply = generate_response_based_on_course_details(user_input, course_details)


    return reply, course_details