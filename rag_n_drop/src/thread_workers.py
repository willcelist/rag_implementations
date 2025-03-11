from PySide6.QtCore import Signal, QThread
from src.rag_utilities import create_v_db
from src.rag_utilities import run_chain


class InvokeModelThread(QThread):
    signalInvokeModel = Signal(object)

    def __init__(self, ll_model, retriever_db, prompt, *args, **kwargs):
        super(InvokeModelThread, self).__init__( *args, **kwargs)
        self.ll_model = ll_model
        self.retriever_db = retriever_db
        self.prompt = prompt


    def run(self):
        response = run_chain(self.ll_model, self.retriever_db, self.prompt)
        self.signalInvokeModel.emit(response)

    def stop(self):
        self.quit()


class CreateVDBThread(QThread):
    signalCreateVDB = Signal(object)

    def __init__(self, doc_path, *args, **kwargs):
        super(CreateVDBThread, self).__init__( *args, **kwargs)
        self.doc_path = doc_path

    def run(self):
        retriever = create_v_db(self.doc_path)
        self.signalCreateVDB.emit(retriever)

    def stop(self):
        self.quit()

