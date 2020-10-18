# based on https://doc.qt.io/archives/qtjambi-4.5.2_01/com/trolltech/qt/qtjambi-syntaxhighlighter-code.html

from collections import namedtuple

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QColor, QFont
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox


class Highlighter(QSyntaxHighlighter):
    Rule = namedtuple('HighlightingRule', ['pattern', 'format'])

    def __init__(self, parent):
        super().__init__(parent)
        self.highlightingRules = []
        
        self.keywordFormat = QTextCharFormat()
        self.classFormat = QTextCharFormat()
        self.commentFormat = QTextCharFormat()
        self.quotationFormat = QTextCharFormat()
        self.functionFormat = QTextCharFormat()
        
        brush = QBrush(Qt.darkBlue,Qt.SolidPattern)
        self.keywordFormat.setForeground(brush)
        self.keywordFormat.setFontWeight(QFont.Bold)
        
        keywords = ["abstract", "continue", "for", "new",
                    "switch", "assert", "default", "goto",
                    "package", "synchronized", "boolean",
                    "do", "if", "private", "this", "break",
                    "double", "implements", "protected",
                    "throw", "byte", "else", "import",
                    "public", "throws", "case", "enum",
                    "instanceof", "return", "transient",
                    "catch", "extends", "int", "short",
                    "try", "char", "final", "interface",
                    "static", "void", "class", "finally",
                    "long", "strictfp", "volatile", "const",
                    "float", "native", "super", "while"]

        for keyword in keywords:
            pattern = QRegExp("\\b" + keyword + "\\b")
            rule = Highlighter.Rule(pattern, self.keywordFormat)
            self.highlightingRules.append(rule)
        
        brush = QBrush(Qt.darkMagenta)
        pattern = QRegExp("\\bQ[A-Za-z]+\\b")
        self.classFormat.setForeground(brush)
        self.classFormat.setFontWeight(QFont.Bold)
        rule = Highlighter.Rule(pattern, self.classFormat)
        self.highlightingRules.append(rule)
        
        brush = QBrush(Qt.gray, Qt.SolidPattern)
        pattern = QRegExp("//[^\n]*")
        self.commentFormat.setForeground(brush)
        rule = Highlighter.Rule(pattern, self.commentFormat)
        self.highlightingRules.append(rule)
        
        brush = QBrush(Qt.blue, Qt.SolidPattern)
        pattern = QRegExp("\".*\"")
        pattern.setMinimal(True)
        self.quotationFormat.setForeground(brush)
        rule = Highlighter.Rule(pattern, self.quotationFormat)
        self.highlightingRules.append(rule)
        
        brush = QBrush(Qt.darkGreen, Qt.SolidPattern)
        pattern = QRegExp("\\b[A-Za-z0-9_]+(?=\\()")
        self.functionFormat.setForeground(brush)
        self.functionFormat.setFontItalic(True)
        rule = Highlighter.Rule(pattern, self.functionFormat)
        self.highlightingRules.append(rule)
        
        self.commentStartExpression = QRegExp("/\\*")
        self.commentEndExpression = QRegExp("\\*/")
    
    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = rule.pattern
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)
        
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)
        
        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()
            self.setFormat(startIndex, commentLength, self.commentFormat)
            startIndex = self.commentStartExpression.indexIn(text, startIndex + commentLength)


class ShowSourceDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        
        font = QFont()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)
        
        self.editor = QTextEdit()
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        self.editor.setFont(font)

        self.highlighter = Highlighter(self.editor.document())
        
        self.editor.setReadOnly(True)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        
        layout.addWidget(self.editor)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        self.setMinimumSize(500, 800)
    
    def set_class_name(self, class_name):
        self.setWindowTitle("Source code for {}.java".format(class_name))
    
    def set_source(self, source):
        self.editor.setText(source)
