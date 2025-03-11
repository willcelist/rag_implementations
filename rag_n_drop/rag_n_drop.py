import os
import sys
import os
import shutil
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QKeyEvent, QColor,QTextCursor, QCursor, QTextCharFormat
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel, QPdfDocumentRenderOptions
from PySide6.QtPdfWidgets import QPdfView, QPdfPageSelector
from src.utilities import load_llm_model
from src.thread_workers import InvokeModelThread, CreateVDBThread
from PySide6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout,
                               QVBoxLayout, QWidget, QTextEdit, QFileDialog,
                               QLabel, QScrollArea, QSizePolicy, QPushButton)


class PDFAnalysis(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pdf_RAG_gui")
        self.setGeometry(100, 50, 1400, 700)

        self.central_widget = QWidget()
        self.central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central_widget)
        self.mainHLayout = QHBoxLayout()
        self.vRightLayout = QVBoxLayout()
        self.vLeftLayout = QVBoxLayout()
        self.searchBtnsLayout = QHBoxLayout()
        self.central_widget.setLayout(self.mainHLayout)
        self.pdf_path = ''

        self.label = QLabel("""Drag and drop a PDF file \n or \n Click to browse your documents""")
        self.label.setStyleSheet(" font-size: 20px; font-family: Avenir;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.responsesTextEdit = QTextEdit()
        self.responsesTextEdit.setReadOnly(True)
        self.promptTextEdit = QTextEdit()
        self.promptTextEdit.installEventFilter(self)
        self.scrollAreaOutput = QScrollArea()
        self.scrollAreaInput = QScrollArea()
        self.scrollAreaOutput.horizontalScrollBar().setEnabled(False)
        self.scrollAreaOutput.horizontalScrollBar().setHidden(True)
        self.scrollAreaOutput.setWidgetResizable(True)
        self.scrollAreaInput.setWidgetResizable(True)
        self.scrollAreaOutput.setBackgroundRole(QPalette.ColorRole.Dark)
        self.mainHLayout.addWidget(self.label)
        self.mainHLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pdf_view = QPdfView()

        self.ll_model = load_llm_model()

        self.invokeModelThread = InvokeModelThread(self.ll_model, None, None)
        self.invokeModelThread.signalInvokeModel.connect(self.write_invoke_response)

        self.createVDBThread = CreateVDBThread('')
        self.createVDBThread.signalCreateVDB.connect(self.update_retriever)

        self.submitPromptBtn = QPushButton('>')
        self.submitPromptBtn.clicked.connect(self.submit_prompt)

        self.labelRefSearch = QLabel('References search')
        self.dummyLabel = QLabel('')
        self.labelRefSearch.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.searchPrevBtn = QPushButton('<')
        self.searchNextBtn = QPushButton('>')
        self.searchPrevBtn.clicked.connect(self.prev_context_str)
        self.searchNextBtn.clicked.connect(self.next_context_str)
        self.context_strs = ''
        self.document = QPdfDocument()
        self.search_idx = 0

        self.label.mousePressEvent = self.explore_for_pdf

        self.blueColor = QColor(0, 145, 255)
        self.greenColor = QColor(10, 255, 180)

        self.setAcceptDrops(True)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.KeyPress) and (obj is self.promptTextEdit):
            if isinstance(event, QKeyEvent):
                if (event.key() == Qt.Key.Key_Return == Qt.Key.Key_Return) or (event.key() == Qt.Key.Key_Enter):
                    self.submit_prompt()
                    return True
        return super().eventFilter(obj, event)

    def submit_prompt(self):
        new_prompt = self.promptTextEdit.toPlainText()
        if new_prompt.endswith('\n'):
            new_prompt = new_prompt.rstrip('\n')
        if new_prompt:
            self.responsesTextEdit.append('\n')
            self.responsesTextEdit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.responsesTextEdit.setTextColor(self.greenColor)
            self.responsesTextEdit.append(new_prompt)
            self.responsesTextEdit.append('\n')

            self.promptTextEdit.setText('')
            self.promptTextEdit.setDisabled(True)
            self.submitPromptBtn.setDisabled(True)

            self.invokeModelThread.prompt = new_prompt
            self.invokeModelThread.start()

            self.responsesTextEdit.verticalScrollBar().setValue(
                self.responsesTextEdit.verticalScrollBar().maximum())



    def prev_context_str(self):
        pass

    def next_context_str(self):
        print('idx: ', self.search_idx)
        search_model = QPdfSearchModel(self)
        search_model.setDocument(self.document)
        search_model.setSearchString(self.context_strs[self.search_idx])
        self.pdf_view.setSearchModel(search_model)
        self.search_idx += 1


    def explore_for_pdf(self, event):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PDF Files (*.pdf)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith('.pdf'):
                self.pdf_path = file_path
                self.display_pdf(file_path)


    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.pdf'):
                self.pdf_path = file_path
                self.display_pdf(file_path)

            else:
                self.label.setText("""Dropped file is not PDF \n 
                Please drag and drop a PDF file \n or 
                \n Click to browse your documents""")

    def write_invoke_response(self, response_txt):
        self.context_strs = response_txt[1]
        self.responsesTextEdit.append('\n')
        self.responsesTextEdit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.responsesTextEdit.setTextColor(self.blueColor)
        self.responsesTextEdit.append(response_txt[0])
        self.responsesTextEdit.append('\n')
        self.promptTextEdit.setDisabled(False)
        self.submitPromptBtn.setDisabled(False)
        self.invokeModelThread.stop()
        self.responsesTextEdit.verticalScrollBar().setValue(
            self.responsesTextEdit.verticalScrollBar().maximum())
        if self.context_strs:
            self.searchNextBtn.setDisabled(False)

    def update_retriever(self, retriever):
        self.invokeModelThread.retriever_db = retriever
        self.createVDBThread.stop()
        self.promptTextEdit.setDisabled(True)
        self.submitPromptBtn.setDisabled(True)
        self.responsesTextEdit.append('Your document text was successfully indexed.\n'
                                      'You can now start to chat with your document!')
        self.promptTextEdit.setDisabled(False)
        self.submitPromptBtn.setDisabled(False)

    def update_layout(self, file_path):
        self.createVDBThread.doc_path = file_path
        self.createVDBThread.start()

        self.promptTextEdit.setDisabled(True)
        self.submitPromptBtn.setDisabled(True)

        self.mainHLayout.removeWidget(self.label)
        self.scrollAreaOutput.setWidget(self.responsesTextEdit)
        self.responsesTextEdit.setTextColor(self.blueColor)
        self.responsesTextEdit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.responsesTextEdit.setText("\n")
        self.responsesTextEdit.append("Please wait while your data is indexed.")

        self.scrollAreaInput.setWidget(self.promptTextEdit)

        self.vRightLayout.addWidget(self.scrollAreaOutput, stretch=1)
        self.vRightLayout.addWidget(self.scrollAreaInput)
        self.vRightLayout.addWidget(self.submitPromptBtn)

        self.mainHLayout.addLayout(self.vRightLayout)

    def display_pdf(self, file_path):
        self.label.setDisabled(True)
        self.label.setText('')
        self.setAcceptDrops(False)
        self.document.load(file_path)

        self.vLeftLayout.addWidget(self.pdf_view)
        self.searchBtnsLayout.addWidget(self.dummyLabel)
        self.searchBtnsLayout.addWidget(self.labelRefSearch)
        self.searchBtnsLayout.addWidget(self.searchPrevBtn)
        self.searchBtnsLayout.addWidget(self.searchNextBtn)
        self.searchPrevBtn.setDisabled(True)
        self.searchNextBtn.setDisabled(True)
        self.vLeftLayout.addLayout(self.searchBtnsLayout)
        self.mainHLayout.addLayout(self.vLeftLayout)

        self.pdf_view.renderFlags = QPdfDocumentRenderOptions.Rotation.Clockwise90
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.update_layout(file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFAnalysis()
    window.show()
    if os.path.isdir('../cdb'):
        shutil.rmtree('../cdb')
    sys.exit(app.exec())


