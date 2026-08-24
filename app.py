import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader




load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        api_key = ""
os.environ["GOOGLE_API_KEY"] = api_key

st.set_page_config(page_title="Travel RAG Assistant")
st.title("AI Travel Concierge — Document Chat")

if not api_key:
    st.error("No API key found. Check your .env file.")
    st.stop()

uploaded_file = st.file_uploader("Upload a travel PDF (itinerary, guide, brochure)", type="pdf")

if uploaded_file:
    if "retriever" not in st.session_state or st.session_state.get("last_file") != uploaded_file.name:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        loader = PyPDFLoader("temp.pdf")
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)

        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        st.session_state.retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        st.session_state.last_file = uploaded_file.name

    retriever = st.session_state.retriever
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    st.success("Document processed. Ask away.")

    if "history" not in st.session_state:
        st.session_state.history = []

    # Display chat history
    for q, a in st.session_state.history:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.write(a)

    query = st.chat_input("Ask something about your travel document...")
    if query:
        with st.spinner("Thinking..."):
            relevant_docs = retriever.invoke(query)
            context = "\n\n".join(doc.page_content for doc in relevant_docs)
            prompt = f"Answer the question using only this context:\n\n{context}\n\nQuestion: {query}"
            answer = llm.invoke(prompt).content
        st.session_state.history.append((query, answer))
        st.rerun()
else:
    st.info("Upload a PDF to start chatting.")