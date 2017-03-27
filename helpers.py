from __future__ import print_function

import os
import sys
from shutil import rmtree
import time

from main import get_encoder

from WikiParse.main           import download_wikidump, parse_wikidump, gensim_corpus
from WikiLearn.code.vectorize import doc2vec

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
	def __init__(self, parent=None, window_title=None):
		super(log_window, self).__init__()
		self.window_title = window_title 
		if window_title is None: self.window_title = "Log"
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

	def open_window(self,location=None,restrict=False):
		if location != None: self.move(location)
		self.username_input.setText(self.username)
		self.host_input.setText(self.host)
		self.port_input.setText(self.port)
		self.dbname_input.setText(self.dbname)
		self.password_input.setText(self.password)
		self.password_input.setFocus()

		if restrict:
			self.username_input.setEnabled(False)
			self.host_input.setEnabled(False)
			self.port_input.setEnabled(False)
			self.dbname_input.setEnabled(False)
		else:
			self.username_input.setEnabled(True)
			self.host_input.setEnabled(True)
			self.port_input.setEnabled(True)
			self.dbname_input.setEnabled(True)
		self.show()

	def closeEvent(self,e):
		self.collect_values()
		self.hide()
		self.parent.cred_cancel()

	def keyPressEvent(self,qkeyEvent):
		if qkeyEvent.key()==Qt.Key_Return or qkeyEvent.key()==Qt.Key_Enter:
			self.ok_pressed()

class wikiserver_window(QWidget):
	canceled_wikiserver = pyqtSignal()

	def __init__(self,parent=None):
		super(wikiserver_window,self).__init__()
		self.setMouseTracking(True)
		self.connect(self,SIGNAL("canceled_wikiserver()"),parent.canceled_wikiserver)
		self.parent = parent
		self.user_log = log_window(self,"Connection Log")
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
		if self.connected==False:
			self.hide()
			self.user_log.hide()
			self.canceled_wikiserver.emit()

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
		if get_cred: 
			self.open_location = location
			self.init_vars()
			return
		else:	
			if self.open_location != None: self.move(self.open_location)
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

class parser_worker(QThread):
	done_parsing = pyqtSignal()

	def __init__(self,parent=None):
		QThread.__init__(self,parent)
		self.connect(self,SIGNAL("done_parsing()"),parent.parent.done_parsing)
		self.exiting = False

	def run(self):
		dump_source = str(self.source)
		download_location = "WikiParse/data/corpora/"+dump_source+"/data"

		if self.redownload:
			dump_path = download_wikidump(dump_source,download_location)
		else:
			if os.path.isdir(download_location):
				files = os.listdir(download_location)
				for f in files:
					if f.find(".bz2")!=-1: continue
					if f.find(".xml")!=-1:
						dump_path = download_location+"/"+f
						print(dump_path)
						break

		if self.use_server:
			parsed = parse_wikidump(dump_path,password=self.server_password)
		else:
			parsed = parse_wikidump(dump_path,password="NONE")

		if self.retrain and parsed:
			encoder_directory = 'WikiLearn/data/models/tokenizer'
			get_encoder('text.tsv',True,encoder_directory+'/text',400,10,5,10,10)
			get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
			get_encoder('links.tsv',False,encoder_directory+'/links',400,500,1,5,20)

		self.done_parsing.emit()

class wikiparse_window(QWidget):
	def __init__(self,parent=None):
		super(wikiparse_window,self).__init__()
		self.cred_window = credentials_window(self)
		self.parent = parent
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.server_host = None 
		self.server_username = None 
		self.server_port = None 
		self.server_dbname = None 
		self.server_password = None

		# not all, just most common
		self.wiki_types = [	"simplewiki","enwiki","frwiki","zhwiki","dewiki","ruwiki","itwiki","eswiki","metawiki",
							"ptwiki","jawiki","nlwiki","plwiki","svwiki","shwiki","arwiki","fawiki","ukwiki","cawiki"]

	def init_ui(self):
		self.setWindowTitle("WikiParse Scheduler")
		self.layout = QVBoxLayout(self)

		self.source_label = QLabel("Source:                       ")
		#self.source_input = QLineEdit("simplewiki")
		self.source_input = QComboBox()
		self.source_input.addItems(self.wiki_types)
		self.source_input.setCurrentIndex(0)

		source_layout = QHBoxLayout()
		source_layout.addWidget(self.source_label)
		source_layout.addWidget(self.source_input)
		self.layout.addLayout(source_layout)

		self.redownload_label = QLabel("Re-download: ")
		self.redownload_check = QCheckBox()
		redownload_layout = QHBoxLayout()
		redownload_layout.addWidget(self.redownload_label)
		redownload_layout.addWidget(self.redownload_check)
		self.layout.addLayout(redownload_layout)

		self.server_label = QLabel("Add to server:")
		self.server_check = QCheckBox()
		server_layout = QHBoxLayout()
		server_layout.addWidget(self.server_label)
		server_layout.addWidget(self.server_check)
		self.layout.addLayout(server_layout)

		self.retrain_label = QLabel("Re-train model:")
		self.retrain_check = QCheckBox()
		retrain_layout = QHBoxLayout()
		retrain_layout.addWidget(self.retrain_label)
		retrain_layout.addWidget(self.retrain_check)
		self.layout.addLayout(retrain_layout)

		self.cancel_button = QPushButton("Cancel")
		self.ok_button = QPushButton("Ok")
		button_layout = QHBoxLayout()
		button_layout.addStretch()
		button_layout.addWidget(self.cancel_button)
		button_layout.addWidget(self.ok_button)
		button_layout.addStretch()
		self.layout.addLayout(button_layout)

		self.resize(300,240)

		#self.source_input.textEdited.connect(self.source_changed)
		self.source_input.currentIndexChanged.connect(self.source_changed)
		self.cancel_button.clicked.connect(self.cancel_pressed)
		self.ok_button.clicked.connect(self.ok_pressed)

	def source_changed(self):
		new_text = str(self.source_input.currentText())
		if new_text not in [" ",""]:
			if self.has_data_dump(dump_name=new_text):
				self.redownload_check.setChecked(False)
				self.redownload_check.setEnabled(True)
			else:
				self.redownload_check.setChecked(True)
				self.redownload_check.setEnabled(False)
		else:
			self.redownload_check.setChecked(True)
			self.redownload_check.setEnabled(False)

	def has_data_dump(self,dump_name="simplewiki"):
		dump_dir = "WikiParse/data/corpora/"+dump_name+"/data/"
		if os.path.isdir(dump_dir):
			files = os.listdir(dump_dir)
			for f in files:
				if f.find(".xml")!=-1: return True 
			return False
		else:
			return False

	def open_window(self,location=None):
		if location != None: 
			self.open_location = location
			self.move(location)
		if not self.has_data_dump(): 
			self.redownload_check.setChecked(True)
			self.redownload_check.setEnabled(False)
		else:
			self.redownload_check.setChecked(False)
			self.redownload_check.setEnabled(True)
		self.show()
		self.server_check.setChecked(True)

	def cancel_pressed(self):
		self.back()

	def ok_pressed(self):
		if self.server_check.isChecked():
			self.hide()
			self.cred_window.open_window(self.open_location,restrict=True)
			return
		self.start_execution(use_server=False)

	def start_execution(self,use_server=False):

		if self.retrain_check.isChecked():
			base_model_files = ["authors","categories","category_parents","domains","links","redirects","text","titles","related_text","related_authors"]
			for f in base_model_files:
				if os.path.isfile(f+".tsv"): os.remove(f+".tsv")
			if os.path.isfile("wikiparse.out"): os.remove("wikiparse.out")
			if os.path.isdir("WikiLearn/data"): rmtree("WikiLearn/data")
		
		if self.redownload_check.isChecked():
			if os.path.isdir("WikiParse/data"): rmtree("WikiParse/data")

		self.worker = parser_worker(self)
		self.worker.use_server = use_server
		self.worker.source = str(self.source_input.currentText())
		self.worker.redownload = True if self.redownload_check.isChecked() else False
		if use_server: self.worker.server_password = self.server_password
		self.worker.retrain = True if self.retrain_check.isChecked() else False 
		self.worker.start()
		self.parent.parsing_started()

	def cred_ok(self):
		self.server_host = self.cred_window.host 
		self.server_username = self.cred_window.username 
		self.server_port = self.cred_window.port 
		self.server_dbname = self.cred_window.dbname 
		self.server_password = self.cred_window.password
		self.start_execution(use_server=True)

	def cred_cancel(self):
		self.show()

	def back(self):
		self.hide()
		self.parent.show()

class notification_window(QWidget):
	def __init__(self,parent=None):
		super(notification_window,self).__init__()
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle("Update")
		self.layout = QVBoxLayout(self)
		self.label = QLabel("")
		self.layout.addWidget(self.label)
		self.resize(400,100)

	def set_notification(self,value,location):
		self.move(location)
		self.label.setText(value)
		self.show()

class main_menu(QWidget):

	def __init__(self,parent=None):
		super(main_menu,self).__init__()
		self.notification_gui = notification_window(parent=self)
		self.wikiserver_gui = wikiserver_window(parent=self)
		self.wikiparse_gui = wikiparse_window(parent=self)
		self.wikilearn_gui = None 
		self.init_ui()

	def init_ui(self):
		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Control Panel")
		
		p = self.palette()
		p.setColor(self.backgroundRole(),Qt.white)
		self.setPalette(p)

		pic_row = QHBoxLayout()
		pic_row.addStretch()
		pic = QLabel()
		pic.setPixmap(QPixmap("resources/icon.png"))
		pic_row.addWidget(pic)
		pic_row.addStretch()
		self.layout.addLayout(pic_row)

		wikilearn_row = QHBoxLayout()
		wikiparse_row = QHBoxLayout()
		wikiserver_row = QHBoxLayout()

		wikiserver_row.addStretch()
		wikiparse_row.addStretch()
		wikilearn_row.addStretch()

		self.wikilearn_button = QPushButton("WikiLearn")
		self.wikiparse_button = QPushButton("WikiParse")
		self.wikiserver_button = QPushButton("[WikiServer]")

		self.wikiserver_button.setFixedWidth(200)
		self.wikilearn_button.setFixedWidth(200)
		self.wikiparse_button.setFixedWidth(200)

		#self.wikiparse_button.setStyleSheet("background-color: white")
		#self.wikiserver_button.setStyleSheet("background-color: white")
		#self.wikilearn_button.setStyleSheet("background-color: white")
		
		wikiserver_row.addWidget(self.wikiserver_button)
		wikiparse_row.addWidget(self.wikiparse_button)
		wikilearn_row.addWidget(self.wikilearn_button)

		wikiserver_row.addStretch()
		wikiparse_row.addStretch()
		wikilearn_row.addStretch()

		self.wikilearn_button.clicked.connect(self.open_wikilearn)
		self.wikiparse_button.clicked.connect(self.open_wikiparse)
		self.wikiserver_button.clicked.connect(self.open_wikiserver)

		self.layout.addSpacing(10)
		self.layout.addLayout(wikiserver_row)
		self.layout.addLayout(wikiparse_row)
		self.layout.addLayout(wikilearn_row)
		self.layout.addSpacing(10)

		self.setFixedWidth(400)
		self.setFixedHeight(410)

		framegm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerpt = QApplication.desktop().screenGeometry(screen).center()
		framegm.moveCenter(centerpt)
		self.move(framegm.topLeft())

		self.show()

	def canceled_wikiserver(self):
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
		self.hide()
		my_point = self.rect().topLeft()
		global_point = self.mapToGlobal(my_point)
		self.wikiparse_gui.open_window(location=global_point)

	def open_wikilearn(self):
		pass

	def closeEvent(self,e):
		sys.exit(1)

	def done_parsing(self):
		self.wikiparse_button.setEnabled(True)
		global_point = self.mapToGlobal(self.rect().topLeft())
		self.notification_gui.set_notification("Parsing is complete",global_point)

	def parsing_started(self):
		self.wikiparse_gui.hide()
		self.wikiparse_button.setEnabled(False)
		self.show()
		global_point = self.mapToGlobal(self.rect().topLeft())
		self.notification_gui.set_notification("Parsing has begun, see command line for detail",global_point)

def start_gui():
	global main_menu_window
	app = QApplication(sys.argv)
	f = open("resources/icon.png")
	app.setWindowIcon(QIcon("resources/icon.png"))
	main_menu_window = main_menu(app)
	sys.exit(app.exec_())