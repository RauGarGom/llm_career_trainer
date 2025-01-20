from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv
import psycopg2
from psycopg2.extras import DictCursor
load_dotenv(override=True)

### Environment variables for API keys
os.environ["LANGCHAIN_TRACING_V2"] = "true"
mistral_api_key = os.getenv("MISTRAL_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")



### Loading of the model
model = ChatGroq(model="llama3-8b-8192")

# async def make_request_with_retry(messages, max_retries=5, delay=60):
#     for attempt in range(max_retries):
#         try:
#             response = await model.generate(messages)
#             return response
#         except Exception as e:
#             if "rate limit" in str(e).lower() and attempt < max_retries - 1:
#                 print(f"Rate limit exceeded. Retrying after {delay} seconds...")
#                 await asyncio.sleep(delay)
#             else:
#                 raise
#     raise Exception("Max retries exceeded")


def generate_question():
    df_questions = pd.read_csv('./data/questions.csv')
    question = df_questions.sample(1,ignore_index=True).values[0][0]
    db_insert_values('generate_question','system',question)
    return question


def evaluate_answer_v2(answer,current_question):
    ### Inserts into the db the answer of the user
    db_insert_values('answer_question','user',answer)

    ### Makes a judgamental thought of the answer
    prompt = ChatPromptTemplate.from_template(
        '''
        You are a Data Science techincal interviewer. Make a reasoned evaluation in 100 words or less of the interviewee, based on the answer {answer} from the question {question}.
        Only evaluate the points explicitly mentioned in the question and only evaluate the answer {answer} from the question {question}, disregarding past interactions.
        For example, do not evaluate the lack of an example in the answer if the question did not ask for it. Also, don't ever grade the question.
        '''
        )
    chain = prompt | model | StrOutputParser()
    thought = chain.invoke({"answer": answer,"question":current_question})
    db_insert_values('evaluate_answer','system',thought)

    ### Gives a grade based on the thought
    grade_prompt = ChatPromptTemplate.from_template(
        '''
        Grade the answer for the interviewee, based on the following reasoning given by the interviewer: {reasoning}. Examples: 1/10, 4/10, 10/10. Only give the grade,
        don't explain it.
        '''
        )
    grade_chain = grade_prompt | model | StrOutputParser()
    grade = grade_chain.invoke({"reasoning":thought,"answer": answer, "question": current_question})
    db_insert_values('grade','system',grade)

    ### Takes the thought and continues the interview
    analysis_prompt = ChatPromptTemplate.from_template(
        '''
        Make a following question based on the grade {grade}. If the grade is 5/10 or higher, make the question harder while being related to the
        quesion {question}, while if the grade is lower than 5/10, make another technical question related to Data Science. that must not be
        related to the question {question}, but must always be related to Data Science. Just give the question and be concise. Don't show 
        the grade or the reasoning and just give the question, this is very important.
        ''')
    composed_chain = analysis_prompt | model | StrOutputParser()
    follow_up = composed_chain.invoke({"reasoning": answer, "grade": grade, "question": current_question})
    db_insert_values('follow_up question','system',follow_up)
    return thought, follow_up, grade, answer

def question_explanation(current_question):
    prompt = ChatPromptTemplate.from_template(
        '''
        You are an Data Science teacher. Give a detailed explanation of the question {question}. Focus on what would be worth metioning in a job interview. Don't use more than 500 words.
        '''
        )
    chain = prompt | model | StrOutputParser()
    explanation = chain.invoke({"question":current_question})
    db_insert_values('answer_explanation','system',explanation)
    return explanation

# def interview_training_local():
    system_template = "You are an interviewer for a Data Science position. Evaluate the answer of {answer} and make a follow-up question, but don't explain it. Be concise."
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{answer}")]
    )
    message = [
    SystemMessage("You are an interviewer for a Data Science position. Ask one random technical question and evaluate the answers of the user. Change to another data science question when they ask to.")
    # HumanMessage("What is the question?"),
    ]
    response = model.invoke(message)
    print(response.content)
    prompt = prompt_template.invoke({"answer": input('answer here')})

    response = model.invoke(prompt)
    print(response.content)

def db_connect():
    host = "localhost" ### Change to llm-db.c9egi4wa8bqm.eu-west-1.rds.amazonaws.com for production, localhost for local
    username = "postgres"
    password = os.getenv("LOCAL_POSTGRE_PASS") ### Change to POSTGRE_PASS for production, LOCAL_POSTGRE_PASS for local.
    port = 5432
    conn = psycopg2.connect(
        host=host,
        user=username,
        password=password,
        cursor_factory=DictCursor 
    )
    cursor = conn.cursor()
    return conn, cursor

def db_insert_values(action,llm_user,content):
    conn, cursor = db_connect()
    cursor.execute('''
    INSERT INTO regist (action,llm_user,content)
    VALUES (%s, %s, %s)
    ''',
    (action,llm_user,content)
    )
    conn.commit()
    conn.close()