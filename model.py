from langchain_mistralai import ChatMistralAI
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


### Loading of the model
model = ChatMistralAI(model="mistral-large-latest")



def generate_question():
    df_questions = pd.read_csv('./data/questions.csv')
    question = df_questions.sample(1,ignore_index=True).values[0][0]
    db_insert_values('generate_question','system',question)
    return question


def evaluate_answer_v2(answer,current_question):
    db_insert_values('answer_question','user',answer)
    ''' Makes a judgamental thought of the answer'''
    prompt = ChatPromptTemplate.from_template("You are an Data Science techincal interviewer. Make a brief evaluation of the interviewee, based on the answer {answer} from the question {question}.")
    chain = prompt | model | StrOutputParser()
    thought = chain.invoke({"answer": answer,"question":current_question})
    db_insert_values('evaluate_answer','system',thought)
    ''' Takes the thought and evolves the interview'''
    analysis_prompt = ChatPromptTemplate.from_template("Make a following question based on {reasoning}. Just give the question and be concise.")
    composed_chain = {"reasoning": chain} | analysis_prompt | model | StrOutputParser()
    follow_up = composed_chain.invoke({"answer": answer, "question": current_question})
    db_insert_values('follow_up question','system',follow_up)
    return thought, follow_up 

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