from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
# from langchain_chroma import Chroma ### TODO: Not needed anymore
from pinecone import Pinecone


load_dotenv(override=True)

### Environment and startup variables for API keys

os.environ["LANGCHAIN_TRACING_V2"] = "true"
mistral_api_key = os.getenv("MISTRAL_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
# CHROMA_PATH = "./data/text_db/chroma_vertex" ### TODO: Not needed anymore
DATA_PATH = "data/text_db/raw"


### Loading of the model
# model = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.2)

#####################
#Startup functions
#####################

def load_split_documents():
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf")
    chunks = loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)) ### We do the splitting in the same def as the loading.
    return chunks


#####################
#DB functions
#####################

def db_connect():
    host = os.getenv("DB_HOST", "localhost")  ### Change to llm-db.c9egi4wa8bqm.eu-west-1.rds.amazonaws.com for production, localhost for local
    username = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "") ### Change to POSTGRE_PASS for production, LOCAL_POSTGRE_PASS for local.
    port = os.getenv("DB_PORT", 5432)
    database = os.getenv("DB_NAME", "postgres")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=password,
            cursor_factory=DictCursor
        )
        cursor = conn.cursor()
        return conn, cursor
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None, None

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
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content='''
        You are a Data Science techincal interviewer. Make a reasoned evaluation in 100 words or less of the interviewee, based on the answer {answer} from the question {question}.
        Only evaluate the points explicitly mentioned in the question and only evaluate the answer {answer} from the question {question}, disregarding past interactions.
        For example, do not evaluate the lack of an example in the answer if the question did not ask for it.
                      
        If the answer is irrelevant, nonsensical, makes you doubt about the question or does not address the question, explicitly state that the answer fails to meet the question's requirements.

        INSTRUCTIONS FOR THE EVALUATION:
        **Do not ever grade the question.**
        **Evaluate what the answer explicitly says. If, for example, the answer is "This is an elaborate answer", that answer is probably not responding the question.**
        **If the answer is irrelevant or nonsensical, say so directly.**
        '''
        ),
        HumanMessage(content=answer)
        ])
    chain = prompt | model | StrOutputParser()
    thought = chain.invoke({"answer": answer,"question":current_question})
    db_insert_values('evaluate_answer','system',thought)

    ### Gives a grade based on the thought
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system",'''Give a numerical score the answer for the interviewee from 1 to 10, based on the following reasoning given by the human: {reasoning}. Examples: "1", "4", "10". Only provide a number,
        don't explain it.
        '''),
        ("human",thought)
    ])
    grade_chain = grade_prompt | model | StrOutputParser()
    grade = grade_chain.invoke({"reasoning":thought,"answer": answer, "question": current_question})
    db_insert_values('grade','system',grade)

    ### Takes the thought and continues the interview
    analysis_prompt = ChatPromptTemplate.from_template(
        '''
        Make a following question based on the grade {grade}. If the grade is 5 or higher, make the question harder while being related to the
        quesion {question}, while if the grade is lower than 5, make another technical question related to Data Science. that must not be
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

    Answer the question based on the above context: {question}.
    Only if there is no valid context given, answer the question as if context was not needed.
    """)
    prompt = prompt_template.format(context=results, question=current_question)
    response = model.invoke(prompt)
    ### TODO: insert response into SQL
    return response.content, results


def question_explanation_streaming(embeddings,current_question):
    # pinecone_api_key = os.getenv("PINECONE_API_KEY")
    # pc = Pinecone(api_key=pinecone_api_key)
    # index_name = "quickstart"
    # index = pc.Index(index_name)
    # vector_store = PineconeVectorStore(index=index,embedding=embeddings)
    # results = vector_store.similarity_search(current_question, k=3)
    prompt_template = ChatPromptTemplate.from_template("""
    You are a Data Science professor, that always explains thoroughly the questions. Answer the following question: {question}.
    """)
    prompt = prompt_template.format(question=current_question)
    stream = model.stream(prompt)
    for chunk in stream:
        if hasattr(chunk, 'content'):
            yield chunk.content
        else:
            yield str(chunk)


