from __future__ import print_function

import os
import sys

try:
	import psycopg2
	from psycopg2 import connect as server_connect
except:
	print("Cannot find Python 2.7 library \'psycopg2\', install using pip!")

try:
	from PyQt4 import QtGui, QtCore
	from PyQt4.QtCore import *
	from PyQt4.QtGui import *
except:
	print("Cannot find Python 2.7 library \'PyQt4\', install using pip!")


main_menu_window = ""

class log_window(QWidget):
	def __init__(self, parent=None):
		super(log_window, self).__init__()
		self.initVars()
		self.initUI()

	def initVars(self):
		self.items = []

	def initUI(self):
		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Connection Log")
		self.log = QTextEdit(self)
		self.layout.addWidget(self.log)
		self.resize(400, 600)

	def open(self,location=None):
		if location != None: self.move(location)
		self.show()

	def update(self, new_item):
		self.items.append(new_item)
		self.log.append(new_item)

	def close_window(self):
		self.close()

class credentials_window(QWidget):
	def __init__(self,parent=None):
		super(credentials_window,self).__init__()
		self.parent = parent
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.username = "waynesun95"
		self.host = "aa1bkwdd6xv6rol.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
		self.port = "5432"
		self.dbname = "ebdb"
		self.password = ""

	def init_ui(self):
		self.setWindowTitle("Server Details")
		self.setFixedWidth(400)
		self.setFixedHeight(400)

		self.layout = QVBoxLayout(self)

		self.username_label = QLabel("Username: ")
		self.username_input = QLineEdit()
		username_layout = QHBoxLayout()
		username_layout.addWidget(self.username_label)
		username_layout.addWidget(self.username_input)
		self.layout.addLayout(username_layout)

		self.host_label = QLabel("Host:           ")
		self.host_input = QLineEdit()
		host_layout = QHBoxLayout()
		host_layout.addWidget(self.host_label)
		host_layout.addWidget(self.host_input)
		self.layout.addLayout(host_layout)

		self.port_label = QLabel("Port:           ")
		self.port_input = QLineEdit()
		port_layout = QHBoxLayout()
		port_layout.addWidget(self.port_label)
		port_layout.addWidget(self.port_input)
		self.layout.addLayout(port_layout)

		self.dbname_label = QLabel("dbName:   ")
		self.dbname_input = QLineEdit()
		dbname_layout = QHBoxLayout()
		dbname_layout.addWidget(self.dbname_label)
		dbname_layout.addWidget(self.dbname_input)
		self.layout.addLayout(dbname_layout)

		self.password_label = QLabel("Password: ")
		self.password_input = QLineEdit()
		password_layout = QHBoxLayout()
		password_layout.addWidget(self.password_label)
		password_layout.addWidget(self.password_input)
		self.layout.addLayout(password_layout)

		ok_button = QPushButton("Ok")
		cancel_button = QPushButton("Cancel")

		button_layout = QHBoxLayout()
		button_layout.addStretch()
		button_layout.addWidget(cancel_button)
		button_layout.addWidget(ok_button)
		button_layout.addStretch()
		self.layout.addLayout(button_layout)

		ok_button.clicked.connect(self.ok_pressed)
		cancel_button.clicked.connect(self.cancel_pressed)

	def collect_values(self):
		self.username = str(self.username_input.text())
		self.host = str(self.host_input.text())
		self.port = str(self.port_input.text())
		self.dbname = str(self.dbname_input.text())
		self.password = str(self.password_input.text())

	def ok_pressed(self):
		self.collect_values()
		self.hide()
		self.parent.cred_ok()

	def cancel_pressed(self):
		self.collect_values()
		self.hide()
		self.parent.cred_cancel()

	def open_window(self,location=None):
		if location != None: self.move(location)
		self.username_input.setText(self.username)
		self.host_input.setText(self.host)
		self.port_input.setText(self.port)
		self.dbname_input.setText(self.dbname)
		self.password_input.setText(self.password)
		self.password_input.setFocus()
		self.show()

	def closeEvent(self,e):
		self.collect_values()
		self.hide()
		self.parent.cred_cancel()

	def keyPressEvent(self,qkeyEvent):
		if qkeyEvent.key()==Qt.Key_Return or qkeyEvent.key()==Qt.Key_Enter:
			self.ok_pressed()

class wikiserver_window(QWidget):
	def __init__(self,parent=None):
		super(wikiserver_window,self).__init__()
		self.setMouseTracking(True)
		self.parent = parent
		self.user_log = log_window(self)
		self.cred_window = credentials_window(self)
		
		self.open_location = None # window location of main menu
		self.current_widget = None
		self.current_meta_layout = None
		self.current_meta_widget_1 = None  # first widget from left
		self.current_meta_widget_2 = None
		self.current_meta_widget_3 = None
		self.current_meta_widget_4 = None 
		self.current_meta_widget_5 = None 
		self.current_widget_name = "none"

		self.table_data = None 

		self.server_host = None 
		self.server_username = None 
		self.server_port = None 
		self.server_dbname = None 
		self.server_password = None
		
		self.commands = []
		self.connected = False
		if self.parent==None: self.init_vars()
		self.init_ui()

	def cred_ok(self):
		self.show()
		self.server_host = self.cred_window.host 
		self.server_username = self.cred_window.username 
		self.server_port = self.cred_window.port 
		self.server_dbname = self.cred_window.dbname 
		self.server_password = self.cred_window.password
		self.init_vars(new_credentials=False)
		self.open_window(get_cred=False)

	def cred_cancel(self):
		self.show()
		self.open_window(get_cred=False)

	def init_vars(self,new_credentials=True):
		self.disconnect(False)

		if new_credentials:
			self.hide()
			self.user_log.hide()
			self.cred_window.open_window(location=self.open_location)
			return
		try:
			self.conn = server_connect("user="+self.server_username+" host="+self.server_host+" port="+self.server_port+" password="+self.server_password+" dbname="+self.server_dbname)
		except:
			print("Could not connect to server!")
			return

		self.connected = True
		self.window_title_manager()

	def init_ui(self):

		self.layout = QVBoxLayout(self) # layout for overall window
		self.toolbar = QMenuBar(self) # toolbar on the top of window

		self.min_width = 700
		self.min_height = 500
		self.setMinimumWidth(self.min_width)
		self.setMinimumHeight(self.min_height)
		self.resize(self.min_width,self.min_height)

		os_name = sys.platform
		if os_name in ["linux","linux2","win32"]: self.layout.addSpacing(25)

		self.file_menu = self.toolbar.addMenu("File")
		self.edit_menu = self.toolbar.addMenu("Edit")
		self.tools_menu = self.toolbar.addMenu("Tools")
		self.view_menu = self.toolbar.addMenu("View")
		self.toolbar.setMinimumWidth(self.min_width)

		self.file_menu.addAction("Reconnect (New Credentials)",self.init_vars,QKeySequence("Ctrl+N"))
		self.file_menu.addAction("Reconnect (Prev Credentials)",self.reconnect,QKeySequence("Ctrl+Shift+N"))
		self.file_menu.addAction("Disconnect",self.disconnect,QKeySequence("Ctrl+D"))
		self.file_menu.addSeparator()

		self.file_menu.addAction("Main Menu",self.back,QKeySequence("Ctrl+B"))
		self.file_menu.addAction("Exit",self.exit,QKeySequence("Ctrl+Q"))

		self.view_menu.addAction("Table",self.show_table,QKeySequence("Ctrl+1"))
		self.view_menu.addAction("Control Panel",self.show_control_panel,QKeySequence("Ctrl+2"))

		self.tools_menu.addAction("Search Table",self.table_search,"Ctrl+F")

		if self.parent==None:
			self.window_title_manager()
			self.view_log()
			self.show_table()
		else:
			self.hide()

	def open_window(self,get_cred=True,location=None):
		self.open_location = location
		if get_cred: 
			self.init_vars()
			return
		else:		
			self.show()
			self.view_log()
			self.window_title_manager()
			self.show_table()

	def clear_ui(self):
		if self.current_widget is not None: self.layout.removeWidget(self.current_widget)
		if self.current_meta_layout is not None:
			for i in reversed(range(self.current_meta_layout.count())):
				to_remove = self.current_meta_layout.itemAt(i).widget()
				if to_remove is not None:
					self.current_meta_layout.removeWidget(to_remove)
					to_remove.setParent(None)
			self.layout.removeItem(self.current_meta_layout)
			self.current_meta_layout.deleteLater()

	def show_control_panel(self):
		if self.connected is False: return

		self.clear_ui()

		self.current_meta_layout = QHBoxLayout()
		self.layout.addLayout(self.current_meta_layout)

		self.current_meta_widget_1 = QLabel("Database Size: ")
		self.current_meta_widget_2 = QLineEdit(str(self.get_table_size(pretty=True)))
		self.current_meta_widget_2.setEnabled(False)
		self.current_meta_widget_2.setFixedWidth(100)

		self.current_meta_layout.addWidget(self.current_meta_widget_1)
		self.current_meta_layout.addWidget(self.current_meta_widget_2)
		self.current_meta_layout.addStretch(2)

		self.current_widget = QListWidget()
		self.current_widget.itemDoubleClicked.connect(self.panel_item_selected)

		self.layout.addWidget(self.current_widget,2)

		self.current_widget_name = "panel"

		self.current_widget.addItem("Re-Populate Server")
		self.current_widget.addItem("Clean Repository")

	def panel_item_selected(self):
		return
		'''
		if self.current_widget_name != "panel": return 

		selection = self.current_widget.currentItem().text()

		if selection == "Clean Repository":
		'''

	def back(self):
		if self.parent==None: return

		self.user_log.hide()
		self.hide()
		self.parent.show()

	def table_search(self):
		if self.current_widget_name != "table": return

		while True:
			query, ok = QInputDialog.getText(self,"Search Query","Enter Query: ")
			if not ok: return
			if ok:
				if query in [" ",""]: continue
				query = str(query).lower()
				break

		for y in range(len(self.table_data)):
			for x in range(len(self.table_data[y])):
				cur_item = str(self.table_data[y][x])
				if cur_item.lower() == query:
					self.current_widget.selectRow(y)
					return
		print("No matches found for query \'"+query+"\'")

	def add_command(self,command):
		self.commands.append(command)
		self.user_log.update(command)

	def delete_articles(self):
		if not self.connected: return

		while True:
			resp = raw_input("Are you sure [y/N]: ")
			if resp in ["y","Y"]:
				break
			elif resp in [""," ","N","n"]:
				return

		cursor 	= self.conn.cursor()
		command = "DELETE FROM articles"

		try:
			cursor.execute(command)
			self.conn.commit()
			self.add_command(command)
			self.update_ui()
		except: 
			print("WARNING: Could not delete \'articles\' table!")
		cursor.close()

	def update_ui(self):
		if self.current_widget_name == "table": self.show_table()

	def get_table_size(self,pretty=False):
		cursor 	= self.conn.cursor()
		if pretty==False: command = "SELECT pg_database_size(\'"+self.server_dbname+"\')"
		else: command = "SELECT pg_size_pretty(pg_database_size(\'"+self.server_dbname+"\'))"

		try:
			cursor.execute(command)
			self.add_command(command)
			size = str(cursor.fetchone()[0])
			return size 
		except: print("WARNING: Could not fetch size of database!")
		cursor.close()

	def show_table(self):
		if self.connected is False: return

		if self.current_widget is not None: self.layout.removeWidget(self.current_widget)
		if self.current_meta_layout is not None: self.layout.removeItem(self.current_meta_layout)

		cursor = self.conn.cursor()
		command = "SELECT * FROM articles"

		try:
			cursor.execute(command)
			self.add_command(command)
			data = cursor.fetchall()
			colnames = [col[0] for col in cursor.description]
		except:
			print("WARNING: Could not connect to server!")
			data = None
			colnames = None
		cursor.close()

		if data is not None:
			num_rows = len(data)
			if num_rows==0: print(data)
			num_cols = len(data[0])
		else:
			num_rows = 2
			num_cols = 2

		self.current_meta_layout = QHBoxLayout()
		self.layout.addLayout(self.current_meta_layout)

		self.current_meta_widget_1 = QLabel("Database Size: ")
		self.current_meta_widget_2 = QLineEdit(str(self.get_table_size(pretty=True)))
		self.current_meta_widget_2.setEnabled(False)
		self.current_meta_widget_2.setFixedWidth(100)

		self.current_meta_widget_3 = QPushButton("Insert Item")
		self.current_meta_widget_3.clicked.connect(self.insert_table_item)

		self.current_meta_widget_4 = QPushButton("Delete Item")
		self.current_meta_widget_4.clicked.connect(self.delete_table_item)
		self.current_meta_widget_4.setEnabled(False)

		self.current_meta_widget_5 = QPushButton("Delete Table")
		self.current_meta_widget_5.clicked.connect(self.delete_table_full)

		self.current_meta_layout.addWidget(self.current_meta_widget_1)
		self.current_meta_layout.addWidget(self.current_meta_widget_2)
		self.current_meta_layout.addStretch()
		self.current_meta_layout.addSpacing(20)
		self.current_meta_layout.addWidget(self.current_meta_widget_3)
		self.current_meta_layout.addWidget(self.current_meta_widget_4)
		self.current_meta_layout.addWidget(self.current_meta_widget_5)

		self.current_widget = QTableWidget(num_rows,num_cols)
		self.current_widget.currentCellChanged.connect(self.table_cell_changed)
		self.layout.addWidget(self.current_widget,2)
		self.current_widget_name = "table"

		if colnames is not None:
			colnames_pyqt = QStringList()
			for col in colnames:
				colnames_pyqt.append(col)
			self.current_widget.setHorizontalHeaderLabels(colnames_pyqt)

		for y in range(num_rows):
			for x in range(num_cols):
				table_item = QTableWidgetItem(str(data[y][x]))
				self.current_widget.setItem(y,x,table_item)
		self.table_data = data

	def table_cell_changed(self):
		if self.current_widget_name == "table": self.current_meta_widget_4.setEnabled(True)

	def delete_table_full(self):
		self.delete_articles()

	def delete_table_item(self):
		if self.connected == False: return
		if self.current_widget_name != "table": return 

		cur_row = self.current_widget.currentRow()
		cur_article_id = str(self.current_widget.item(cur_row,1).text())

		command = "DELETE FROM articles WHERE title = \'"+cur_article_id+"\'"
		cursor = self.conn.cursor()

		try:
			cursor.execute(command)
			self.conn.commit()
			cursor.close()
			self.add_command(command)
		except:
			print("WARNING: Could not delete table item!")
			cursor.close()
			return

		self.current_widget.removeRow(cur_row)

	def insert_table_item(self):
		print("not yet implemented")
		pass

	def view_log(self):
		if self.isVisible()==False: return
		my_point = self.rect().topRight()
		global_point = self.mapToGlobal(my_point)
		self.user_log.open(global_point)

	def window_title_manager(self):
		title_str = "PSQL Server Control Panel"
		if self.connected: title_str += " - Connected - "
		else: title_str += " - Disconnected - "
		if self.server_dbname!= None: title_str += self.server_dbname
		self.setWindowTitle(title_str)

	def reconnect(self):
		self.disconnect()
		self.init_vars(new_credentials=False)

	def disconnect(self,update=True):
		if self.connected: 	self.conn.close()
		self.connected 		= False
		if update: 			self.window_title_manager()

	def exit(self):
		self.disconnect(update=False)
		self.user_log.close_window()
		if self.parent==None: sys.exit(1)

	def closeEvent(self,e):
		self.exit()
		return

class main_menu(QWidget):

	def __init__(self,parent=None):
		super(main_menu,self).__init__()
		self.wikiserver_gui = wikiserver_window(parent=self)
		self.wikiparse_gui = None 
		self.wikilearn_gui = None 
		self.init_ui()

	def init_ui(self):
		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Control Panel")
		
		wikilearn_button = QPushButton("WikiLearn")
		wikiparse_button = QPushButton("WikiParse")
		wikiserver_button = QPushButton("[WikiServer]")

		wikilearn_button.clicked.connect(self.open_wikilearn)
		wikiparse_button.clicked.connect(self.open_wikiparse)
		wikiserver_button.clicked.connect(self.open_wikiserver)

		self.layout.addSpacing(10)
		self.layout.addWidget(wikiserver_button)
		self.layout.addWidget(wikiparse_button)
		self.layout.addWidget(wikilearn_button)
		self.layout.addSpacing(10)

		self.setFixedWidth(225)
		self.setFixedHeight(175)
		self.show()

	def keyPressEvent(self,qkeyEvent):
		if qkeyEvent.key()==Qt.Key_Return or qkeyEvent.key()==Qt.Key_Enter:
			self.open_wikiserver()

	def open_wikiserver(self):
		self.hide()
		my_point = self.rect().topLeft()
		global_point = self.mapToGlobal(my_point)
		self.wikiserver_gui.open_window(location=global_point)

	def open_wikiparse(self):
		pass

	def open_wikilearn(self):
		pass

	def closeEvent(self,e):
		'''
		if self.wikiserver_gui is not None: self.wikiserver_gui.exit()
		if self.wikiparse_gui is not None: self.wikiparse_gui.exit()
		if self.wikilearn_gui is not None: self.wikilearn_gui.exit()
		'''
		sys.exit(1)

def start_gui():
	global main_menu_window
	app = QApplication(sys.argv)
	main_menu_window = main_menu(app)
	sys.exit(app.exec_())