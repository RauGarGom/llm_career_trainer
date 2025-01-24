from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_chroma import Chroma
from pinecone import Pinecone


load_dotenv(override=True)

### Environment and startup variables for API keys

os.environ["LANGCHAIN_TRACING_V2"] = "true"
mistral_api_key = os.getenv("MISTRAL_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
CHROMA_PATH = "./data/text_db/chroma_vertex"
DATA_PATH = "data/text_db/raw"


### Loading of the model
model = ChatGroq(model="llama3-8b-8192")

#####################
#Startup functions
#####################

def load_split_documents():
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf")
    chunks = loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)) ### We do the splitting in the same def as the loading.
    return chunks

def chroma_read(chunks, embeddings):
    if os.path.exists(CHROMA_PATH+'/chroma.sqlite3') == True:
        print("Local Chroma DB found. Reading Chroma database...")
        chroma_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        print("Loaded Chroma DB from disk.")
    else:
        print("Local Chroma DB not found. Creating Chroma database...")
        chroma_db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
        print(f"Saved {len(chunks)} to {CHROMA_PATH}")
    return chroma_db


#####################
#DB functions
#####################

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

#####################
#LLM-based functions
#####################

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



def question_explanation(embeddings, current_question):
    ### Connection to Pinecone Vector Store
    print("Loading documents...")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "quickstart"
    index = pc.Index(index_name)
    vector_store = PineconeVectorStore(index=index,embedding=embeddings)
    print("Searching for similar questions...")
    results = vector_store.similarity_search(current_question, k=3)
    print("Creating prompt and invoking model...")
    prompt_template = ChatPromptTemplate.from_template("""
    Answer the question based only on the following context:

    {context}

    ---

    Answer the question based on the above context: {question}
    """)
    prompt = prompt_template.format(context=results, question=current_question)
    response = model.invoke(prompt)
    return response.content, results

