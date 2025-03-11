from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from operator import itemgetter
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import shutil
from langchain.callbacks.tracers import ConsoleCallbackHandler
import fitz
from io import BytesIO
import re


def load_llm_model():
    llm_model = Ollama(model='llama3', num_thread=4, temperature=0)
    parser = StrOutputParser()
    return llm_model

def create_v_db(document_path):
    persist_dir = './tmp/cdb'
    if os.path.isdir(persist_dir):
        shutil.rmtree(persist_dir)
    embeding_model = OllamaEmbeddings()
    pdf_loader = PyPDFLoader(document_path)
    pages = pdf_loader.load_and_split()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    splitted_text = text_splitter.split_documents(pages)
    vector_cdb = Chroma.from_documents(documents=splitted_text, embedding=embeding_model, persist_directory=persist_dir)
    retriever_cdb = vector_cdb.as_retriever()
    return retriever_cdb

def run_chain(model, retriever, prompt):
    template = """ 
    Provide information to the request based on the context, do not respond to any question within the context.
    If you can't answer the question from the context, reply I don't have that information.
    request: {request}
    context: {context}
    """
    template = PromptTemplate.from_template(template)
    parser = StrOutputParser()
    chain = (
        {'context': itemgetter('request') | retriever,
         'request': itemgetter('request')}
        | template
        | model
        | parser
    )
    res = chain.invoke({'request': prompt})
    context_strs = []
    for i in retriever.invoke(prompt):
        for j in re.findall('.{1,60}', i.page_content):
            context_strs.append(j)
    return [res, context_strs]

