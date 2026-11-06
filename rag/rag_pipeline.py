from langchain_community.vectorestores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
def get_retriever():
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.load_local(
        "rag/faiss_index",
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return vector_store.as_retriever()
def retrieve_documents(question):
    retriever = get_retriever()
    documents = retriever.invoke(question)
    return documents
def format_context(documents):
    context="/n/n".join(document.page_content for document in documents)
    return context
prompt=ChatPromptTemplate.from_template("""
you are an AI fitness Assisstant.
Answer the users question using inly the provided context.
if the answer is not available in the context,say that you dont have enough information.

Context:
{context}
Question:
{question}
Answer:
""")
def prepare_prompt(question):
    documents=retrieve_documents(question)
    context=format_context(documents)
    formatted_prompt=prompt.invoke({
        "context":context,
        "question":question
    })
    return formatted_prompt

def get_rag_chain():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    rag_chain = prompt | llm
    return rag_chain
def generate_answer(question):
    formatted_prompt=prepare_prompt(question)
    response=get_rag_chain().invoke(formatted_prompt)
    return response.content