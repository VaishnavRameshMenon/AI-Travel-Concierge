import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

print("Sending request...")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
response = llm.invoke("Say hello in one sentence.")
print("Got response:")
print(response.content)
