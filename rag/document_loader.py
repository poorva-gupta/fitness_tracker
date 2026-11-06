from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

file_path=Path(__file__).parent/"Knowledge_base"/"fitness_guide.pdf"
loader=PyPDFLoader(file_path)
documents=loader.load()

text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
chunks=text_splitter.split_documents(documents)
print(chunks)

embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectors=embedding_model.embed_documents([chunk.page_content for chunk in chunks])
print(vectors)

vector_store=FAISS.from_documents(chunks,embedding_model)
vector_store.save_local("rag/faiss_index")

