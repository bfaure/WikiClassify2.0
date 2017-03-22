from __future__ import print_function

import os
import sys

try:
	import psycopg2
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

class wikiserver_window(QWidget):
	def __init__(self,parent=None):
		super(wikiserver_window,self).__init__()
		self.setMouseTracking(True)
		self.parent = parent
		self.user_log = log_window(self)
		
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
		self.init_vars()
		self.init_ui()

	def init_vars(self,new_credentials=True):
		self.connected = False

		if new_credentials:
			print("\n")
			self.server_host = raw_input("Host [aa1bkwdd6xv6rol.cja4xyhmyefl.us-east-1.rds.amazonaws.com]: ")
			if self.server_host in [" ",""]: self.server_host = "aa1bkwdd6xv6rol.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
			self.server_username = raw_input("Username [waynesun95] \t| ")
			if self.server_username in [" ",""]: self.server_username = "waynesun95"
			self.server_port = raw_input("Port [5432] \t\t| ")
			if self.server_port in [" ",""]: self.server_port = "5432"
			self.server_dbname = raw_input("Database Name [ebdb] \t| ")
			if self.server_dbname in [" ",""]: self.server_dbname = "ebdb"
			while True:
				self.server_password = raw_input("Password \t\t| ")
				if self.server_password not in [" ",""]: break
			print("\n")
		
		try:
			self.conn = psycopg2.connect("user="+self.server_username+" host="+self.server_host+" port="+self.server_port+" password="+self.server_password+" dbname="+self.server_dbname)
		except:
			ans = raw_input("Could not connect to server, try again [Y/n]: ")
			if ans in [" ","","Y","y"]: return self.init_vars()
			else: return

		self.connected = True
		print("Connected to "+self.server_dbname)
		self.window_title_manager()

	def init_ui(self):

		self.layout = QVBoxLayout(self) # layout for overall window
		self.toolbar = QMenuBar(self) # toolbar on the top of window

		self.min_width = 700
		self.min_height = 500
		self.setMinimumWidth(self.min_width)
		self.setMinimumHeight(self.min_height)
		self.resize(self.min_width,self.min_height)
		if os.name=="nt": self.layout.addSpacing(25)

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

		self.tools_menu.addAction("Search Table",self.table_search,"Ctrl+F")

		self.window_title_manager()
		self.view_log()
		self.show_table()

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
		if self.connected: self.conn.close()
		self.connected = False
		if update: self.window_title_manager()

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
		self.wikiserver_gui = wikiserver_window(self)
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
		self.wikiserver_gui.show()
		self.wikiserver_gui.view_log()

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