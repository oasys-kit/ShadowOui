__author__ = 'labx'

import sys
import code
import keyword
import itertools

from PyQt5 import QtGui, QtWidgets

from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtGui import (
    QTextCursor, QFont, QColor, QPalette
)

from PyQt5.QtCore import Qt, QRegExp


def text_format(foreground=Qt.black, weight=QFont.Normal):
    fmt = QtGui.QTextCharFormat()
    fmt.setForeground(QtGui.QBrush(foreground))
    fmt.setFontWeight(weight)
    return fmt


class PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):

        self.keywordFormat = text_format(Qt.blue, QFont.Bold)
        self.stringFormat = text_format(Qt.darkGreen)
        self.defFormat = text_format(Qt.black, QFont.Bold)
        self.commentFormat = text_format(Qt.lightGray)
        self.decoratorFormat = text_format(Qt.darkGray)

        self.keywords = list(keyword.kwlist)

        self.rules = [(QRegExp(r"\b%s\b" % kwd), self.keywordFormat)
                      for kwd in self.keywords] + \
                     [(QRegExp(r"\bdef\s+([A-Za-z_]+[A-Za-z0-9_]+)\s*\("),
                       self.defFormat),
                      (QRegExp(r"\bclass\s+([A-Za-z_]+[A-Za-z0-9_]+)\s*\("),
                       self.defFormat),
                      (QRegExp(r"'.*'"), self.stringFormat),
                      (QRegExp(r'".*"'), self.stringFormat),
                      (QRegExp(r"#.*"), self.commentFormat),
                      (QRegExp(r"@[A-Za-z_]+[A-Za-z0-9_]+"),
                       self.decoratorFormat)]

        self.multilineStart = QRegExp(r"(''')|" + r'(""")')
        self.multilineEnd = QRegExp(r"(''')|" + r'(""")')

        super().__init__(parent)

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            exp = QRegExp(pattern)
            index = exp.indexIn(text)
            while index >= 0:
                length = exp.matchedLength()
                if exp.numCaptures() > 0:
                    self.setFormat(exp.pos(1), len(str(exp.cap(1))), format)
                else:
                    self.setFormat(exp.pos(0), len(str(exp.cap(0))), format)
                index = exp.indexIn(text, index + length)

        # Multi line strings
        start = self.multilineStart
        end = self.multilineEnd

        self.setCurrentBlockState(0)
        startIndex, skip = 0, 0
        if self.previousBlockState() != 1:
            startIndex, skip = start.indexIn(text), 3
        while startIndex >= 0:
            endIndex = end.indexIn(text, startIndex + skip)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLen = len(text) - startIndex
            else:
                commentLen = endIndex - startIndex + 3
            self.setFormat(startIndex, commentLen, self.stringFormat)
            startIndex, skip = (start.indexIn(text,
                                              startIndex + commentLen + 3),
                                3)


class PythonScriptEditor(QtWidgets.QPlainTextEdit):
    INDENT = 4

    def lastLine(self):
        text = str(self.toPlainText())
        pos = self.textCursor().position()
        index = text.rfind("\n", 0, pos)
        text = text[index: pos].lstrip("\n")
        return text

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            text = self.lastLine()
            indent = len(text) - len(text.lstrip())
            if text.strip() == "pass" or text.strip().startswith("return "):
                indent = max(0, indent - self.INDENT)
            elif text.strip().endswith(":"):
                indent += self.INDENT
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
        elif event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.INDENT)
        elif event.key() == Qt.Key_Backspace:
            text = self.lastLine()
            if text and not text.strip():
                cursor = self.textCursor()
                for i in range(min(self.INDENT, len(text))):
                    cursor.deletePreviousChar()
            else:
                super().keyPressEvent(event)

        else:
            super().keyPressEvent(event)


class PythonConsole(QtWidgets.QPlainTextEdit, code.InteractiveConsole):
    def __init__(self, locals=None, parent=None):
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        code.InteractiveConsole.__init__(self, locals)
        self.history, self.historyInd = [""], 0
        self.loop = self.interact()
        next(self.loop)

    def setLocals(self, locals):
        self.locals = locals

    def interact(self, banner=None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        cprt = ('Type "help", "copyright", "credits" or "license" '
                'for more information.')
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write("%s\n" % str(banner))
        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                self.new_prompt(prompt)
                yield
                try:
                    line = self.raw_input(prompt)
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

    def raw_input(self, prompt):
        input = str(self.document().lastBlock().previous().text())
        return input[len(prompt):]

    def new_prompt(self, prompt):
        self.write(prompt)
        self.newPromptPos = self.textCursor().position()

    def write(self, data):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.insertText(data)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def push(self, line):
        if self.history[0] != line:
            self.history.insert(0, line)
        self.historyInd = 0

        saved = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = self, self
            return code.InteractiveConsole.push(self, line)
        finally:
            sys.stdout, sys.stderr = saved

    def setLine(self, line):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.setPosition(self.newPromptPos, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(line)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.write("\n")
            next(self.loop)
        elif event.key() == Qt.Key_Up:
            self.historyUp()
        elif event.key() == Qt.Key_Down:
            self.historyDown()
        elif event.key() == Qt.Key_Tab:
            self.complete()
        elif event.key() in [Qt.Key_Left, Qt.Key_Backspace]:
            if self.textCursor().position() > self.newPromptPos:
                QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

    def historyUp(self):
        self.setLine(self.history[self.historyInd])
        self.historyInd = min(self.historyInd + 1, len(self.history) - 1)

    def historyDown(self):
        self.setLine(self.history[self.historyInd])
        self.historyInd = max(self.historyInd - 1, 0)

    def complete(self):
        pass

    def _moveCursorToInputLine(self):
        """
        Move the cursor to the input line if not already there. If the cursor
        if already in the input line (at position greater or equal to
        `newPromptPos`) it is left unchanged, otherwise it is moved at the
        end.

        """
        cursor = self.textCursor()
        pos = cursor.position()
        if pos < self.newPromptPos:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

    def pasteCode(self, source):
        """
        Paste source code into the console.
        """
        self._moveCursorToInputLine()

        for line in interleave(source.splitlines(), itertools.repeat("\n")):
            if line != "\n":
                self.insertPlainText(line)
            else:
                self.write("\n")
                next(self.loop)

    def insertFromMimeData(self, source):
        """
        Reimplemented from QPlainTextEdit.insertFromMimeData.
        """
        if source.hasText():
            self.pasteCode(str(source.text()))
            return


def interleave(seq1, seq2):
    """
    Interleave elements of `seq2` between consecutive elements of `seq1`.

        >>> list(interleave([1, 3, 5], [2, 4]))
        [1, 2, 3, 4, 5]

    """
    iterator1, iterator2 = iter(seq1), iter(seq2)
    leading = next(iterator1)
    for element in iterator1:
        yield leading
        yield next(iterator2)
        leading = element

    yield leading


class Script(object):
    Modified = 1
    MissingFromFilesystem = 2

    def __init__(self, name, script, flags=0, filename=None):
        self.name = name
        self.script = script
        self.flags = flags
        self.filename = filename


class ScriptItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def displayText(self, script, locale):
        if script.flags & Script.Modified:
            return "*" + script.name
        else:
            return script.name

    def paint(self, painter, option, index):
        script = index.data(Qt.DisplayRole)

        if script.flags & Script.Modified:
            option = QtWidgets.QStyleOptionViewItem(option)
            option.palette.setColor(QPalette.Text, QColor(Qt.red))
            option.palette.setColor(QPalette.Highlight, QColor(Qt.darkRed))
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        return QtWidgets.QLineEdit(parent)

    def setEditorData(self, editor, index):
        script = index.data(Qt.DisplayRole)
        editor.setText(script.name)

    def setModelData(self, editor, model, index):
        model[index.row()].name = str(editor.text())


def select_row(view, row):
    """
    Select a `row` in an item view
    """
    selmodel = view.selectionModel()
    selmodel.select(view.model().index(row, 0),
                    QItemSelectionModel.ClearAndSelect)
