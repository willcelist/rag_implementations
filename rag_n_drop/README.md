RAG PDF Analysis with Llama and Chroma DB

This project implements RAG (Retrieval Augmented Generation) analysis on PDF files using Llama and Chroma DB, and provides a graphical user interface (GUI) using PySide6.

Overview
When you launch the project, you'll see a simple window where you can open your PDF files. 
The program will then extract text from these PDFs, break it into chunks, and build a vector database using ChromaDB.
Then, you can prompt the agent, the responses will be rooted in the content extracted from the PDFs.

You can download the folder using this tool:
https://download-directory.github.io/
and copying the link to this folder:
https://github.com/willcelist/rag_implementations/tree/main/rag_n_drop

Optionaly you can dowload the whole repo:
git clone https://github.com/willcelist/rag_implementations.git

Install dependencies:
You'll need to ensure you install Ollama, and download the Llama3 model by running:
ollama pull llama3
ollama run llama3
pip install -r requirements.txt

Usage
Run the GUI application:
python main.py
Use the interface to upload PDF files and perform RAG.

