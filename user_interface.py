# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'user_interface.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ui_main_window(object):
    def setupUi(self, ui_main_window):
        ui_main_window.setObjectName("ui_main_window")
        ui_main_window.setWindowModality(QtCore.Qt.WindowModal)
        ui_main_window.resize(995, 749)
        ui_main_window.setWindowTitle("Proto Plugin")
        ui_main_window.setAccessibleName("")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(ui_main_window)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.menu_widget = QtWidgets.QListWidget(ui_main_window)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.menu_widget.sizePolicy().hasHeightForWidth())
        self.menu_widget.setSizePolicy(sizePolicy)
        self.menu_widget.setMinimumSize(QtCore.QSize(100, 200))
        self.menu_widget.setMaximumSize(QtCore.QSize(153, 16777215))
        self.menu_widget.setStyleSheet("QListWidget{\n"
"    background-color: rgb(69, 69, 69, 220);\n"
"    outline: 0;\n"
"}\n"
"QListWidget::item {\n"
"    color: white;\n"
"    padding: 3px;\n"
"}\n"
"QListWidget::item::selected {\n"
"    color: black;\n"
"    background-color:palette(Window);\n"
"    padding-right: 0px;\n"
"}")
        self.menu_widget.setFrameShape(QtWidgets.QFrame.Box)
        self.menu_widget.setLineWidth(0)
        self.menu_widget.setIconSize(QtCore.QSize(32, 32))
        self.menu_widget.setUniformItemSizes(True)
        self.menu_widget.setObjectName("menu_widget")
        item = QtWidgets.QListWidgetItem()
        self.menu_widget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.menu_widget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.menu_widget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        self.menu_widget.addItem(item)
        self.horizontalLayout_2.addWidget(self.menu_widget)
        self.content_widget = QtWidgets.QVBoxLayout()
        self.content_widget.setObjectName("content_widget")
        self.main_scroll = QtWidgets.QScrollArea(ui_main_window)
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setObjectName("main_scroll")
        self.main_scroll_inside = QtWidgets.QWidget()
        self.main_scroll_inside.setGeometry(QtCore.QRect(0, 0, 832, 745))
        self.main_scroll_inside.setMinimumSize(QtCore.QSize(783, 0))
        self.main_scroll_inside.setObjectName("main_scroll_inside")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.main_scroll_inside)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.stacked_panels_widget = QtWidgets.QStackedWidget(self.main_scroll_inside)
        self.stacked_panels_widget.setObjectName("stacked_panels_widget")
        self.create_example_data = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.create_example_data.sizePolicy().hasHeightForWidth())
        self.create_example_data.setSizePolicy(sizePolicy)
        self.create_example_data.setObjectName("create_example_data")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.create_example_data)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.create_example_data)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.comboBox = QtWidgets.QComboBox(self.create_example_data)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comboBox)
        self.label_3 = QtWidgets.QLabel(self.create_example_data)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.mQgsFileWidget = gui.QgsFileWidget(self.create_example_data)
        self.mQgsFileWidget.setUseLink(False)
        self.mQgsFileWidget.setFullUrl(False)
        self.mQgsFileWidget.setDialogTitle("")
        self.mQgsFileWidget.setStorageMode(gui.QgsFileWidget.SaveFile)
        self.mQgsFileWidget.setObjectName("mQgsFileWidget")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.mQgsFileWidget)
        self.label_2 = QtWidgets.QLabel(self.create_example_data)
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.verticalLayout_2.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(self.create_example_data)
        self.pushButton.setAutoDefault(True)
        self.pushButton.setDefault(False)
        self.pushButton.setFlat(False)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.stacked_panels_widget.addWidget(self.create_example_data)
        self.create_graph = QtWidgets.QWidget()
        self.create_graph.setObjectName("create_graph")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.create_graph)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.create_graph)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.formLayoutWidget_2 = QtWidgets.QWidget(self.tab)
        self.formLayoutWidget_2.setGeometry(QtCore.QRect(9, 9, 791, 161))
        self.formLayoutWidget_2.setObjectName("formLayoutWidget_2")
        self.formLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_2)
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_4 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_4.setObjectName("label_4")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.label_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.mFeaturePickerWidget = gui.QgsFeaturePickerWidget(self.formLayoutWidget_2)
        self.mFeaturePickerWidget.setObjectName("mFeaturePickerWidget")
        self.horizontalLayout_5.addWidget(self.mFeaturePickerWidget)
        self.toolButton = QtWidgets.QToolButton(self.formLayoutWidget_2)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout_5.addWidget(self.toolButton)
        self.formLayout_2.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_5)
        self.label_6 = QtWidgets.QLabel(self.formLayoutWidget_2)
        self.label_6.setObjectName("label_6")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.label_6)
        self.mQgsFileWidget_2 = gui.QgsFileWidget(self.formLayoutWidget_2)
        self.mQgsFileWidget_2.setUseLink(False)
        self.mQgsFileWidget_2.setFullUrl(False)
        self.mQgsFileWidget_2.setDialogTitle("")
        self.mQgsFileWidget_2.setStorageMode(gui.QgsFileWidget.SaveFile)
        self.mQgsFileWidget_2.setObjectName("mQgsFileWidget_2")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.mQgsFileWidget_2)
        self.checkBox = QtWidgets.QCheckBox(self.formLayoutWidget_2)
        self.checkBox.setObjectName("checkBox")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.checkBox)
        self.mGroupBox = gui.QgsCollapsibleGroupBox(self.tab)
        self.mGroupBox.setGeometry(QtCore.QRect(10, 180, 791, 251))
        self.mGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.mGroupBox.setFlat(False)
        self.mGroupBox.setCheckable(False)
        self.mGroupBox.setCollapsed(False)
        self.mGroupBox.setScrollOnExpand(False)
        self.mGroupBox.setSaveCollapsedState(True)
        self.mGroupBox.setSaveCheckedState(False)
        self.mGroupBox.setObjectName("mGroupBox")
        self.formLayoutWidget_3 = QtWidgets.QWidget(self.mGroupBox)
        self.formLayoutWidget_3.setGeometry(QtCore.QRect(10, 30, 771, 211))
        self.formLayoutWidget_3.setObjectName("formLayoutWidget_3")
        self.formLayout_3 = QtWidgets.QFormLayout(self.formLayoutWidget_3)
        self.formLayout_3.setContentsMargins(0, 0, 0, 0)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_7 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_7.setObjectName("label_7")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.mFieldComboBox = gui.QgsFieldComboBox(self.formLayoutWidget_3)
        self.mFieldComboBox.setObjectName("mFieldComboBox")
        self.formLayout_3.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.mFieldComboBox)
        self.label_5 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_5.setObjectName("label_5")
        self.formLayout_3.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.mFeaturePickerWidget_2 = gui.QgsFeaturePickerWidget(self.formLayoutWidget_3)
        self.mFeaturePickerWidget_2.setObjectName("mFeaturePickerWidget_2")
        self.horizontalLayout_6.addWidget(self.mFeaturePickerWidget_2)
        self.toolButton_2 = QtWidgets.QToolButton(self.formLayoutWidget_3)
        self.toolButton_2.setObjectName("toolButton_2")
        self.horizontalLayout_6.addWidget(self.toolButton_2)
        self.formLayout_3.setLayout(5, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout_6)
        self.label_10 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_10.setObjectName("label_10")
        self.formLayout_3.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.label_10)
        self.comboBox_4 = QtWidgets.QComboBox(self.formLayoutWidget_3)
        self.comboBox_4.setObjectName("comboBox_4")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.formLayout_3.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.comboBox_4)
        self.label_12 = QtWidgets.QLabel(self.formLayoutWidget_3)
        self.label_12.setObjectName("label_12")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_12)
        self.comboBox_6 = QtWidgets.QComboBox(self.formLayoutWidget_3)
        self.comboBox_6.setObjectName("comboBox_6")
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.comboBox_6)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.tab_2)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(10, 10, 791, 641))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.textBrowser = QtWidgets.QTextBrowser(self.verticalLayoutWidget_2)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_3.addWidget(self.textBrowser)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout_7.addLayout(self.verticalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.pushButton_4 = QtWidgets.QPushButton(self.create_graph)
        self.pushButton_4.setCheckable(False)
        self.pushButton_4.setChecked(False)
        self.pushButton_4.setAutoRepeat(False)
        self.pushButton_4.setAutoExclusive(False)
        self.pushButton_4.setAutoDefault(True)
        self.pushButton_4.setDefault(False)
        self.pushButton_4.setFlat(False)
        self.pushButton_4.setObjectName("pushButton_4")
        self.horizontalLayout_3.addWidget(self.pushButton_4)
        self.pushButton_3 = QtWidgets.QPushButton(self.create_graph)
        self.pushButton_3.setCheckable(False)
        self.pushButton_3.setDefault(False)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_3.addWidget(self.pushButton_3)
        self.verticalLayout_7.addLayout(self.horizontalLayout_3)
        self.stacked_panels_widget.addWidget(self.create_graph)
        self.ogdf_analysis = QtWidgets.QWidget()
        self.ogdf_analysis.setObjectName("ogdf_analysis")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.ogdf_analysis)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.ogdf_analysis)
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.formLayoutWidget_7 = QtWidgets.QWidget(self.tab_5)
        self.formLayoutWidget_7.setGeometry(QtCore.QRect(9, 9, 791, 161))
        self.formLayoutWidget_7.setObjectName("formLayoutWidget_7")
        self.formLayout_7 = QtWidgets.QFormLayout(self.formLayoutWidget_7)
        self.formLayout_7.setContentsMargins(0, 0, 0, 0)
        self.formLayout_7.setObjectName("formLayout_7")
        self.label_13 = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.label_13.setObjectName("label_13")
        self.formLayout_7.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.label_13)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.mFeaturePickerWidget_5 = gui.QgsFeaturePickerWidget(self.formLayoutWidget_7)
        self.mFeaturePickerWidget_5.setObjectName("mFeaturePickerWidget_5")
        self.horizontalLayout_9.addWidget(self.mFeaturePickerWidget_5)
        self.toolButton_5 = QtWidgets.QToolButton(self.formLayoutWidget_7)
        self.toolButton_5.setObjectName("toolButton_5")
        self.horizontalLayout_9.addWidget(self.toolButton_5)
        self.formLayout_7.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_9)
        self.label_17 = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.label_17.setObjectName("label_17")
        self.formLayout_7.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.label_17)
        self.comboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_7)
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.formLayout_7.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.comboBox_2)
        self.label_14 = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.label_14.setObjectName("label_14")
        self.formLayout_7.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.label_14)
        self.mQgsFileWidget_4 = gui.QgsFileWidget(self.formLayoutWidget_7)
        self.mQgsFileWidget_4.setUseLink(False)
        self.mQgsFileWidget_4.setFullUrl(False)
        self.mQgsFileWidget_4.setDialogTitle("")
        self.mQgsFileWidget_4.setStorageMode(gui.QgsFileWidget.SaveFile)
        self.mQgsFileWidget_4.setObjectName("mQgsFileWidget_4")
        self.formLayout_7.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.mQgsFileWidget_4)
        self.mGroupBox_3 = gui.QgsCollapsibleGroupBox(self.tab_5)
        self.mGroupBox_3.setGeometry(QtCore.QRect(10, 180, 791, 421))
        self.mGroupBox_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.mGroupBox_3.setFlat(False)
        self.mGroupBox_3.setCheckable(False)
        self.mGroupBox_3.setCollapsed(False)
        self.mGroupBox_3.setScrollOnExpand(False)
        self.mGroupBox_3.setSaveCollapsedState(True)
        self.mGroupBox_3.setSaveCheckedState(False)
        self.mGroupBox_3.setObjectName("mGroupBox_3")
        self.formLayoutWidget_8 = QtWidgets.QWidget(self.mGroupBox_3)
        self.formLayoutWidget_8.setGeometry(QtCore.QRect(10, 30, 771, 211))
        self.formLayoutWidget_8.setObjectName("formLayoutWidget_8")
        self.formLayout_8 = QtWidgets.QFormLayout(self.formLayoutWidget_8)
        self.formLayout_8.setContentsMargins(0, 0, 0, 0)
        self.formLayout_8.setObjectName("formLayout_8")
        self.label_15 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.label_15.setObjectName("label_15")
        self.formLayout_8.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_15)
        self.mFieldComboBox_3 = gui.QgsFieldComboBox(self.formLayoutWidget_8)
        self.mFieldComboBox_3.setObjectName("mFieldComboBox_3")
        self.formLayout_8.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.mFieldComboBox_3)
        self.label_16 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.label_16.setObjectName("label_16")
        self.formLayout_8.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_16)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.mFeaturePickerWidget_6 = gui.QgsFeaturePickerWidget(self.formLayoutWidget_8)
        self.mFeaturePickerWidget_6.setObjectName("mFeaturePickerWidget_6")
        self.horizontalLayout_10.addWidget(self.mFeaturePickerWidget_6)
        self.toolButton_6 = QtWidgets.QToolButton(self.formLayoutWidget_8)
        self.toolButton_6.setObjectName("toolButton_6")
        self.horizontalLayout_10.addWidget(self.toolButton_6)
        self.formLayout_8.setLayout(5, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout_10)
        self.label_9 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.label_9.setObjectName("label_9")
        self.formLayout_8.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.label_9)
        self.comboBox_3 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.formLayout_8.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.comboBox_3)
        self.label_11 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.label_11.setObjectName("label_11")
        self.formLayout_8.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_11)
        self.comboBox_5 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.comboBox_5.setObjectName("comboBox_5")
        self.comboBox_5.addItem("")
        self.comboBox_5.addItem("")
        self.formLayout_8.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.comboBox_5)
        self.tabWidget_2.addTab(self.tab_5, "")
        self.tab_6 = QtWidgets.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.verticalLayoutWidget_6 = QtWidgets.QWidget(self.tab_6)
        self.verticalLayoutWidget_6.setGeometry(QtCore.QRect(10, 10, 791, 641))
        self.verticalLayoutWidget_6.setObjectName("verticalLayoutWidget_6")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_6)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.textBrowser_3 = QtWidgets.QTextBrowser(self.verticalLayoutWidget_6)
        self.textBrowser_3.setObjectName("textBrowser_3")
        self.verticalLayout_11.addWidget(self.textBrowser_3)
        self.tabWidget_2.addTab(self.tab_6, "")
        self.verticalLayout_8.addWidget(self.tabWidget_2)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem2)
        self.pushButton_5 = QtWidgets.QPushButton(self.ogdf_analysis)
        self.pushButton_5.setObjectName("pushButton_5")
        self.horizontalLayout_11.addWidget(self.pushButton_5)
        self.pushButton_2 = QtWidgets.QPushButton(self.ogdf_analysis)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_11.addWidget(self.pushButton_2)
        self.verticalLayout_8.addLayout(self.horizontalLayout_11)
        self.verticalLayout_9.addLayout(self.verticalLayout_8)
        self.stacked_panels_widget.addWidget(self.ogdf_analysis)
        self.options = QtWidgets.QWidget()
        self.options.setObjectName("options")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.options)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox = QtWidgets.QGroupBox(self.options)
        self.groupBox.setObjectName("groupBox")
        self.formLayoutWidget_5 = QtWidgets.QWidget(self.groupBox)
        self.formLayoutWidget_5.setGeometry(QtCore.QRect(10, 30, 791, 251))
        self.formLayoutWidget_5.setObjectName("formLayoutWidget_5")
        self.formLayout_5 = QtWidgets.QFormLayout(self.formLayoutWidget_5)
        self.formLayout_5.setContentsMargins(0, 0, 0, 0)
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_8 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.label_8.setObjectName("label_8")
        self.formLayout_5.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.lineEdit = QtWidgets.QLineEdit(self.formLayoutWidget_5)
        self.lineEdit.setObjectName("lineEdit")
        self.formLayout_5.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.lineEdit)
        self.verticalLayout_4.addWidget(self.groupBox)
        self.verticalLayout_10.addLayout(self.verticalLayout_4)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.options)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_10.addWidget(self.buttonBox)
        self.stacked_panels_widget.addWidget(self.options)
        self.verticalLayout_5.addWidget(self.stacked_panels_widget)
        self.main_scroll.setWidget(self.main_scroll_inside)
        self.content_widget.addWidget(self.main_scroll)
        self.horizontalLayout_2.addLayout(self.content_widget)

        self.retranslateUi(ui_main_window)
        self.menu_widget.setCurrentRow(-1)
        self.stacked_panels_widget.setCurrentIndex(3)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ui_main_window)
        ui_main_window.setTabOrder(self.main_scroll, self.menu_widget)

    def retranslateUi(self, ui_main_window):
        _translate = QtCore.QCoreApplication.translate
        __sortingEnabled = self.menu_widget.isSortingEnabled()
        self.menu_widget.setSortingEnabled(False)
        item = self.menu_widget.item(0)
        item.setText(_translate("ui_main_window", "Create example data"))
        item = self.menu_widget.item(1)
        item.setText(_translate("ui_main_window", "Create graph"))
        item = self.menu_widget.item(2)
        item.setText(_translate("ui_main_window", "OGDF analysis"))
        item = self.menu_widget.item(3)
        item.setText(_translate("ui_main_window", "Options"))
        self.menu_widget.setSortingEnabled(__sortingEnabled)
        self.label.setText(_translate("ui_main_window", "Example data set"))
        self.comboBox.setItemText(0, _translate("ui_main_window", "airports"))
        self.comboBox.setItemText(1, _translate("ui_main_window", "streets"))
        self.label_3.setText(_translate("ui_main_window", "Destination"))
        self.pushButton.setText(_translate("ui_main_window", "Create"))
        self.label_4.setText(_translate("ui_main_window", "Vector layer (only points or lines)"))
        self.toolButton.setText(_translate("ui_main_window", "..."))
        self.label_6.setText(_translate("ui_main_window", "Destination"))
        self.checkBox.setText(_translate("ui_main_window", "Random graph"))
        self.mGroupBox.setTitle(_translate("ui_main_window", "Advanced Parameters"))
        self.label_7.setText(_translate("ui_main_window", "Cost field [optional]"))
        self.label_5.setText(_translate("ui_main_window", "Rasterdata [optional]"))
        self.toolButton_2.setText(_translate("ui_main_window", "..."))
        self.label_10.setText(_translate("ui_main_window", "Rasterdata type [optional]"))
        self.comboBox_4.setItemText(0, _translate("ui_main_window", "elevation"))
        self.comboBox_4.setItemText(1, _translate("ui_main_window", "prohibited area"))
        self.comboBox_4.setItemText(2, _translate("ui_main_window", "cost"))
        self.label_12.setText(_translate("ui_main_window", "Distance"))
        self.comboBox_6.setItemText(0, _translate("ui_main_window", "euclidian"))
        self.comboBox_6.setItemText(1, _translate("ui_main_window", "shortest path"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("ui_main_window", "Parameters"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("ui_main_window", "Log"))
        self.pushButton_4.setText(_translate("ui_main_window", "Show"))
        self.pushButton_3.setText(_translate("ui_main_window", "Create"))
        self.label_13.setText(_translate("ui_main_window", "Graph or vector layer (only points or lines)"))
        self.toolButton_5.setText(_translate("ui_main_window", "..."))
        self.label_17.setText(_translate("ui_main_window", "Analysis"))
        self.comboBox_2.setItemText(0, _translate("ui_main_window", "Spanner"))
        self.label_14.setText(_translate("ui_main_window", "Destination"))
        self.mGroupBox_3.setTitle(_translate("ui_main_window", "Advanced Parameters"))
        self.label_15.setText(_translate("ui_main_window", "Cost field [optional]"))
        self.label_16.setText(_translate("ui_main_window", "Rasterdata [optional]"))
        self.toolButton_6.setText(_translate("ui_main_window", "..."))
        self.label_9.setText(_translate("ui_main_window", "Rasterdata type [optional]"))
        self.comboBox_3.setItemText(0, _translate("ui_main_window", "elevation"))
        self.comboBox_3.setItemText(1, _translate("ui_main_window", "prohibited area"))
        self.comboBox_3.setItemText(2, _translate("ui_main_window", "cost"))
        self.label_11.setText(_translate("ui_main_window", "Distance"))
        self.comboBox_5.setItemText(0, _translate("ui_main_window", "euclidian"))
        self.comboBox_5.setItemText(1, _translate("ui_main_window", "shortest path"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_5), _translate("ui_main_window", "Parameters"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_6), _translate("ui_main_window", "Log"))
        self.pushButton_5.setText(_translate("ui_main_window", "Show"))
        self.pushButton_2.setText(_translate("ui_main_window", "Run"))
        self.groupBox.setTitle(_translate("ui_main_window", "Server settings"))
        self.label_8.setText(_translate("ui_main_window", "Server address"))
from qgis import gui
