from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import getpass
import os
from dotenv import load_dotenv, find_dotenv
import psycopg2
from psycopg2.extras import DictCursor
load_dotenv(override=True)

### Environment variables for API keys
os.environ["LANGCHAIN_TRACING_V2"] = "true"
mistral_api_key = os.getenv("MISTRAL_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

### Loading of the model
model = ChatMistralAI(model="mistral-large-latest")

def generate_question():
    system_template = "You are an interviewer for a Data Science position. Ask one random technical question."
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template)]
    )
    message = [
        SystemMessage("You are an interviewer for a Data Science position. Ask one random technical question.")
    ]
    response = model.invoke(message)
    db_insert_values('generate_question','system',response.content)
    return response.content

def evaluate_answer(answer):
    db_insert_values('answer_question','user',answer)
    system_template = "You are an interviewer for a Data Science position. Evaluate the answer of {answer} and make a follow-up question, but don't explain it. Be concise."
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{answer}")]
    )
    prompt = prompt_template.invoke({"answer": answer})
    response = model.invoke(prompt)
    db_insert_values('evaluate_answer','system',response.content)
    return response.content

def interview_training_local():
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
    host = "llm-db.c9egi4wa8bqm.eu-west-1.rds.amazonaws.com"
    username = "postgres"
    password = os.getenv("POSTGRE_PASS")
    port = 5432
    conn = psycopg2.connect(
        host=host,
        user=username,
        password=password,
        cursor_factory=DictCursor  # Devuelve filas como diccionarios
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