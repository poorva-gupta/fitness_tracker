from langchain_community.vectorstores import FAISS
from rag.document_loader import chunks,embedding_model

vector_store=FAISS.from_documents(chunks,embedding_model)
vector_store.save_local("rag/faiss_index")
print