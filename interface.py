from __future__ import print_function

import os
import sys
from shutil import rmtree
import time

import webbrowser

try:
	import psutil
except:
	print("Cannot find Python 2.7 library\'psutil\', install using pip!")
	sys.exit(0)

from time import time
from time import sleep

#from main import get_encoder, get_google_encoder
#from main import get_encoder
from pathfinder import PriorityQueue, rectify_path, get_transition_cost, elem_t

from WikiParse.main           import download_wikidump, parse_wikidump, expand_bz2 #,gensim_corpus
#from WikiLearn.code.vectorize import word2vec
from WikiLearn.code.vectorize import doc2vec

try:
	import psycopg2
	from psycopg2 import connect as server_connect
except:
	print("Cannot find Python 2.7 library \'psycopg2\', install using pip!")
	sys.exit(0)

try:
	from PyQt4 import QtGui, QtCore
	from PyQt4.QtCore import *
	from PyQt4.QtGui import *
except:
	print("Cannot find Python 2.7 library \'PyQt4\', install using \'apt-get install python-qt4\'!")
	sys.exit(0)


print("\nNOTE: To interface with server C++ PSQL Bindings must be installed.")
print("      1. \'sudo apt-get install libpq-dev\'")
print("      2. \'sudo apt-get install libpqxx-dev\'")
print("      Ignore if both are already installed.\n")


main_menu_window = ""

class cred_t(object):
	def __init__(self):
		self.server_host     = "NONE"
		self.server_username = "NONE"
		self.server_port     = "NONE"
		self.server_dbname   = "NONE"
		self.server_password = "NONE"

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
		self.host 	  = "aa9qiuq51j8l7b.cja4xyhmyefl.us-east-1.rds.amazonaws.com"
		self.port     = "5432"
		self.dbname   = "ebdb"
		self.password = ""

	def init_ui(self):
		self.setWindowTitle("Server Details")
		self.setFixedWidth(400)
		self.setFixedHeight(400)

		self.layout = QVBoxLayout(self)

		self.username_label = QLabel("Username: ")
		self.username_input = QLineEdit()
		username_layout     = QHBoxLayout()
		username_layout.addWidget(self.username_label)
		username_layout.addWidget(self.username_input)
		self.layout.addLayout(username_layout)

		self.host_label = QLabel("Host:           ")
		self.host_input = QLineEdit()
		host_layout     = QHBoxLayout()
		host_layout.addWidget(self.host_label)
		host_layout.addWidget(self.host_input)
		self.layout.addLayout(host_layout)

		self.port_label = QLabel("Port:           ")
		self.port_input = QLineEdit()
		port_layout     = QHBoxLayout()
		port_layout.addWidget(self.port_label)
		port_layout.addWidget(self.port_input)
		self.layout.addLayout(port_layout)

		self.dbname_label = QLabel("dbName:   ")
		self.dbname_input = QLineEdit()
		dbname_layout     = QHBoxLayout()
		dbname_layout.addWidget(self.dbname_label)
		dbname_layout.addWidget(self.dbname_input)
		self.layout.addLayout(dbname_layout)

		self.password_label = QLabel("Password: ")
		self.password_input = QLineEdit()
		password_layout     = QHBoxLayout()
		password_layout.addWidget(self.password_label)
		password_layout.addWidget(self.password_input)
		self.layout.addLayout(password_layout)

		ok_button     = QPushButton("Ok")
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
		self.host     = str(self.host_input.text())
		self.port     = str(self.port_input.text())
		self.dbname   = str(self.dbname_input.text())
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
		self.parent      = parent
		self.user_log    = log_window(self,"Connection Log")
		self.cred_window = credentials_window(self)

		self.open_location         = None # window location of main menu
		self.current_widget        = None
		self.current_meta_layout   = None
		self.current_meta_widget_1 = None  # first widget from left
		self.current_meta_widget_2 = None
		self.current_meta_widget_3 = None
		self.current_meta_widget_4 = None
		self.current_meta_widget_5 = None
		self.current_widget_name   = "none"

		self.table_data = None

		self.server_host     = None
		self.server_username = None
		self.server_port     = None
		self.server_dbname   = None
		self.server_password = None

		self.commands  = []
		self.connected = False
		if self.parent==None: self.init_vars()
		self.init_ui()

	def cred_ok(self):
		self.show()
		self.server_host     = self.cred_window.host
		self.server_username = self.cred_window.username
		self.server_port     = self.cred_window.port
		self.server_dbname   = self.cred_window.dbname
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

		self.layout  = QVBoxLayout(self) # layout for overall window
		self.toolbar = QMenuBar(self) # toolbar on the top of window

		self.min_width  = 700
		self.min_height = 500
		self.setMinimumWidth(self.min_width)
		self.setMinimumHeight(self.min_height)
		self.resize(self.min_width,self.min_height)

		os_name = sys.platform
		if os_name in ["linux","linux2","win32"]: self.layout.addSpacing(25)

		self.file_menu  = self.toolbar.addMenu("File")
		self.edit_menu  = self.toolbar.addMenu("Edit")
		self.tools_menu = self.toolbar.addMenu("Tools")
		self.view_menu  = self.toolbar.addMenu("View")
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
		pass

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

		cursor 	= self.conn.cursor()
		command = "DELETE FROM articles;"

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
		else: 			  command = "SELECT pg_size_pretty(pg_database_size(\'"+self.server_dbname+"\'))"

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

		cursor  = self.conn.cursor()
		command = "SELECT * FROM articles"

		try:
			cursor.execute(command)
			self.add_command(command)
			data 	 = cursor.fetchall()
			colnames = [col[0] for col in cursor.description]
		except:
			print("WARNING: Could not connect to server!")
			data     = None
			colnames = None
		cursor.close()

		if data is not None:
			num_rows = len(data)
			if num_rows==0:
				print("WARNING: Got empty articles table!")
				return
			num_cols = len(data[0])
		else:
			num_rows = 2
			num_cols = 2

		self.current_meta_layout   = QHBoxLayout()
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

		self.current_widget      = QTableWidget(num_rows,num_cols)
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
		if self.connected == False: 			return
		if self.current_widget_name != "table": return

		cur_row 		= self.current_widget.currentRow()
		cur_article_id 	= str(self.current_widget.item(cur_row,1).text())

		command = "DELETE FROM articles WHERE title = \'"+cur_article_id+"\'"
		cursor 	= self.conn.cursor()

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

	def view_log(self):
		if self.isVisible()==False: return
		my_point     = self.rect().topRight()
		global_point = self.mapToGlobal(my_point)
		self.user_log.open(global_point)

	def window_title_manager(self):
		title_str 					  = "PSQL Server Control Panel"
		if self.connected: title_str += " - Connected - "
		else: title_str 			 += " - Disconnected - "

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

class parser_worker(QThread):
	done_parsing = pyqtSignal()

	def __init__(self,parent=None):
		QThread.__init__(self,parent)
		self.connect(self,SIGNAL("done_parsing()"),parent.parent.done_parsing)
		self.exiting = False

	def run(self):
		dump_source 	  = str(self.source)
		download_location = "WikiParse/data/corpora/"+dump_source+"/data"

		if self.redownload: dump_path = download_wikidump(dump_source,download_location)
		else:
			if os.path.isdir(download_location):
				files     = os.listdir(download_location)
				dump_path = None
				bz2_path  = None
				for f in files:
					if f.find(".bz2")!=-1:
						bz2_path  = download_location+"/"+f
						continue
					if f.find(".xml")!=-1:
						dump_path = download_location+"/"+f
						print(dump_path)
						break
				if dump_path==None and bz2_path!=None: dump_path = expand_bz2(bz2_path)

		parsed = parse_wikidump(dump_path,creds=self.creds,version=dump_source)

		if self.retrain and parsed:
			pass
			#encoder_directory = 'WikiLearn/data/models/tokenizer'
			#get_encoder()

		self.done_parsing.emit()

class wikiparse_window(QWidget):
	def __init__(self,parent=None):
		super(wikiparse_window,self).__init__()
		self.cred_window = credentials_window(self)
		self.parent 	 = parent
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.server_host 		= None
		self.server_username 	= None
		self.server_port 		= None
		self.server_dbname 		= None
		self.server_password 	= None

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
		self.source_input.setToolTip("Names of popular Wikipedia versions")
		self.source_input.setCurrentIndex(0)

		source_layout = QHBoxLayout()
		source_layout.addWidget(self.source_label)
		source_layout.addWidget(self.source_input)
		self.layout.addLayout(source_layout)

		self.redownload_label = QLabel("Re-download: ")
		self.redownload_check = QCheckBox()
		self.redownload_check.setToolTip("Disabled if no prior version found")

		redownload_layout = QHBoxLayout()
		redownload_layout.addWidget(self.redownload_label)
		redownload_layout.addWidget(self.redownload_check)
		self.layout.addLayout(redownload_layout)

		self.server_label = QLabel("Add to server:")
		self.server_check = QCheckBox()
		server_layout     = QHBoxLayout()
		server_layout.addWidget(self.server_label)
		server_layout.addWidget(self.server_check)
		self.layout.addLayout(server_layout)

		self.retrain_label = QLabel("Re-train model:")
		self.retrain_check = QCheckBox()
		retrain_layout     = QHBoxLayout()
		retrain_layout.addWidget(self.retrain_label)
		retrain_layout.addWidget(self.retrain_check)
		self.layout.addLayout(retrain_layout)

		self.cancel_button = QPushButton("Cancel")
		self.ok_button     = QPushButton("Ok")
		button_layout      = QHBoxLayout()
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
		else: return False

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

	def cancel_pressed(self):
		self.back()

	def ok_pressed(self):
		if self.server_check.isChecked():
			self.hide()
			self.cred_window.open_window(self.open_location,restrict=True)
			return
		self.start_execution(use_server=False)

	def start_execution(self,use_server=False):

		enforce_recompile=True
		if enforce_recompile:
			print("Enforcing re-compile of wikiparse.out")
			if os.path.isfile("wikiparse.out"): os.remove("wikiparse.out")

		if self.retrain_check.isChecked():
			base_model_files = ["authors","categories","category_parents","domains","links","redirects","text","titles","related_text","related_authors"]
			for f in base_model_files:
				if os.path.isfile(f+".tsv"): os.remove(f+".tsv")
			if os.path.isfile("wikiparse.out"): os.remove("wikiparse.out")
			if os.path.isdir("WikiLearn/data"): rmtree("WikiLearn/data")

		src = str(self.source_input.currentText())
		if self.redownload_check.isChecked():
			if os.path.isdir("WikiParse/data/corpora/"+src): rmtree("WikiParse/data/corpora/"+src)

		self.worker 			= parser_worker(self)
		self.worker.source 		= src
		self.worker.redownload 	= True if self.redownload_check.isChecked() else False

		exec_creds = cred_t()
		if use_server:
			exec_creds.server_host 		= self.server_host
			exec_creds.server_username 	= self.server_username
			exec_creds.server_port 		= self.server_port
			exec_creds.server_dbname 	= self.server_dbname
			exec_creds.server_password 	= self.server_password

		self.worker.creds = exec_creds
		self.worker.retrain = True if self.retrain_check.isChecked() else False
		self.worker.start()
		self.parent.parsing_started()

	def cred_ok(self):
		self.server_host     = self.cred_window.host
		self.server_username = self.cred_window.username
		self.server_port     = self.cred_window.port
		self.server_dbname   = self.cred_window.dbname
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
		self.layout.addSpacing(10)
		self.layout.addWidget(QLabel("You may close this window"))
		self.resize(400,100)

	def set_notification(self,value,location):
		self.move(location)
		self.label.setText(value)
		self.resize(self.sizeHint())
		self.show()

class wikilearn_worker(QThread):
	got_path = pyqtSignal()
	failure = pyqtSignal()
	got_result = pyqtSignal()

	def __init__(self,parent=None):
		QThread.__init__(self,parent)
		self.parent=parent
		self.connect(self,SIGNAL("got_path()"),self.parent.got_path)
		self.connect(self,SIGNAL("failure()"),self.parent.no_path)
		self.connect(self,SIGNAL("got_result()"),self.parent.got_sum)
		self.exiting = False
		self.valid = False
		self.start_query = None
		self.end_query = None
		self.encoder = None
		self.job = None
		self.branching_factor = None
		self.weight = None

	def run(self):
		if self.job=="path":
			start_query = self.start_query
			end_query = self.end_query
			encoder = self.encoder
			branching_factor = self.branching_factor
			weight = self.weight

			start_vector = encoder.get_nearest_word(start_query,topn = branching_factor)
			end_vector   = encoder.get_nearest_word(end_query,topn = branching_factor)
			if start_vector == None:
				self.offender = "query1"

			if end_vector == None:
				self.offender = "query2"

			if start_vector==None or end_vector==None:
				self.failure.emit()
				return

			frontier = PriorityQueue()
			start_elem = elem_t(start_query,parent=None,cost=get_transition_cost(start_query,end_query,encoder))
			frontier.push(start_elem)
			cost_list = {}
			cost_list[start_query] = 0
			path_end = start_elem
			base_cost = 0
			explored = []
			return_code = "NONE"
			while True:
				if self.exiting:
					return
				sys.stdout.flush()
				if frontier.length() == 0:
					return_code = "NOT FOUND"
					break
				cur_node = frontier.pop()
				cur_word = cur_node.value
				explored.append(cur_word)
				if cur_word == end_query:
					path_end = cur_node
					break
				neighbors = encoder.get_nearest_word(cur_word,topn=branching_factor)
				if neighbors == None:
					continue
				base_cost = cost_list[cur_word]
				for neighbor_word in neighbors:
					if cur_word == neighbor_word:
						continue
					cost = base_cost + get_transition_cost(cur_word,neighbor_word,encoder)
					new_elem = elem_t(neighbor_word,parent=cur_node,cost=cost)
					new_elem.column_offset = neighbors.index(neighbor_word)
					if (neighbor_word not in cost_list or cost<cost_list[neighbor_word]) and neighbor_word not in explored:
						cost_list[neighbor_word] = cost
						new_elem.cost = cost + (float(weight)*(get_transition_cost(neighbor_word,end_query,encoder)))
						frontier.push(new_elem)

			solution_path,offsets = rectify_path(path_end)
			self.solution_path = solution_path
			self.valid = True
			self.got_path.emit()

		if self.job=="algebra":
			if len(self.positive_words)!=0 and len(self.negative_words)!=0:
				try:
					output = self.text_encoder.model.most_similar_cosmul(positive=self.positive_words,negative=self.negative_words)[0][0]
				except:
					output = "ERROR (1)"
			elif len(self.positive_words)!=0:
				try:
					output = self.text_encoder.model.most_similar_cosmul(positive=self.positive_words)[0][0]
				except:
					output = "ERROR (2)"
			elif len(self.negative_words)!=0:
				try:
					output = self.text_encoder.model.most_similar(negative=self.negative_words)[0][0]
				except:
					output = "ERROR (3)"
			self.output = output
			self.got_result.emit()

class wikilearn_window(QWidget):

	def __init__(self,parent=None):
		super(wikilearn_window,self).__init__()
		self.parent = parent
		self.notification_gui = notification_window(self)
		self.workers = []
		self.init_ui()

	def close_workers(self):
		for f in self.workers:
			f.exiting = True

	def return_to_main_menu(self):
		self.hide()
		self.parent.show()
		self.close_workers()

	def init_vars(self):
		# commented out region is the former code used to load our custom models
		global_point = self.mapToGlobal(self.rect().topLeft())
		encoder_directory = 'WikiLearn/data/models/tokenizer'
		if not os.path.isdir(encoder_directory):
			self.notification_gui.set_notification("Could not locate \""+encoder_directory+"\"",global_point)
			self.return_to_main_menu()
			return False

		if not os.path.isfile('titles.tsv'):
			self.notification_gui.set_notification("Could not locate titles.tsv",global_point)
			self.return_to_main_menu()
			return False

		try:
			self.text_encoder     = get_encoder('text.tsv',True,encoder_directory+"/text",300,10,5,20,10)
			#self.category_encoder = get_encoder('categories.tsv',False,encoder_directory+'/categories',200,300,1,5,20)
			#self.link_encoder     = get_encoder('links.tsv',False,encoder_directory+'/links',200,300,1,5,20)
			#self.doc_ids          = dict([x.strip().split('\t') for x in open('titles.tsv')])
		except:
			self.notification_gui.set_notification("Could not load encoders",global_point)
			self.return_to_main_menu()
			return False

		'''
		# for loading google model...
		encoder_directory = 'WikiLearn/data/models/word2vec'
		self.text_encoder = get_google_encoder()
		'''

		return True

	def init_ui(self):
		self.layout = QVBoxLayout(self)
		self.setWindowTitle("WikiLearn Tools")

		self.tab_widget = QTabWidget()

		self.layout.addWidget(self.tab_widget)

		self.path_widget = QWidget() # parent for layout in path tab
		self.add_widget  = QWidget() # parent for layout in add tab

		self.path_layout = QVBoxLayout(self.path_widget) # path tab layout

		self.add_tab_layout = QVBoxLayout(self.add_widget) # add tab layout
		self.add_layout = QVBoxLayout()
		self.add_lower = QVBoxLayout()

		self.add_tab_layout.addLayout(self.add_layout)
		self.add_tab_layout.addStretch(1)
		self.add_tab_layout.addLayout(self.add_lower)

		self.tab_widget.addTab(self.path_widget,"Path Finder")
		self.tab_widget.addTab(self.add_widget,"Word Summation")

		path_upper_row = QHBoxLayout()
		path_upper_row.addWidget(QLabel("Query 1: "))

		self.path_query_1 = QLineEdit()
		self.path_query_1.setPlaceholderText("Query 1...")
		self.path_query_1.setFixedWidth(100)
		self.path_query_1.textEdited.connect(self.path_query_changed)
		path_upper_row.addWidget(self.path_query_1)
		path_upper_row.addStretch(2)

		self.path_layout.addLayout(path_upper_row)

		self.path_result_widget = QTextEdit()
		self.path_result_widget.setEnabled(False)
		self.path_layout.addWidget(self.path_result_widget,2)

		path_lower_row = QHBoxLayout()
		path_lower_row.addWidget(QLabel("Query 2: "))

		self.path_query_2 = QLineEdit()
		self.path_query_2.setPlaceholderText("Query 2..")
		self.path_query_2.setFixedWidth(100)
		self.path_query_2.textEdited.connect(self.path_query_changed)
		path_lower_row.addWidget(self.path_query_2)
		path_lower_row.addStretch()

		self.path_layout.addLayout(path_lower_row)

		divider = QFrame()
		divider.setFrameShape(QFrame.HLine)
		self.path_layout.addWidget(divider)

		path_parameter_row = QHBoxLayout()

		path_parameter_row.addWidget(QLabel("Cost: "))

		self.path_cost_input = QLineEdit()
		self.path_cost_input.setText("5")
		self.path_cost_input.textEdited.connect(self.path_query_changed)
		path_parameter_row.addWidget(self.path_cost_input)

		path_parameter_row.addSpacing(50)
		path_parameter_row.addWidget(QLabel("Branching Factor: "))

		self.path_branching_factor_input = QLineEdit()
		self.path_branching_factor_input.setText("100")
		self.path_branching_factor_input.textEdited.connect(self.path_query_changed)
		path_parameter_row.addWidget(self.path_branching_factor_input)

		self.path_layout.addLayout(path_parameter_row)

		self.tab_widget.setCurrentIndex(0)

		self.word_inputs = []

		divider2 = QFrame()
		divider2.setFrameShape(QFrame.HLine)
		self.add_lower.addWidget(divider2)

		self.add_lower_row = QHBoxLayout()
		self.add_lower_row.addWidget(QLabel("Result: "))

		self.add_result = QLineEdit()
		self.add_result.setEnabled(False)
		self.add_lower_row.addWidget(self.add_result)

		self.add_lower_row.addSpacing(40)

		self.cancel_add_button = QPushButton("Reset")
		self.cancel_add_button.clicked.connect(self.reset_add)
		self.add_lower_row.addWidget(self.cancel_add_button)

		self.add_lower.addLayout(self.add_lower_row)

		self.width  = 500
		self.height = 500

		self.resize(self.width,self.height)

		self.tab_widget.currentChanged.connect(self.current_tab_changed)

	def reset_add(self):
		self.current_tab_changed()

	def keyPressEvent(self,e):
		if e.key() in [Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter]:
			if self.tab_widget.currentIndex()==1:
				if len(self.word_inputs)!=0:
					if self.word_inputs[-2].hasFocus: self.word_inputs[-1].setFocus()
					#return self.add_input_generator()

	def current_tab_changed(self):
		# if the "Word Algebra" tab...
		if self.tab_widget.currentIndex()==1:
			self.add_result.setText("")

			# remove all items in add tab
			for i in reversed(range(self.add_layout.count())):
				self.add_layout.itemAt(i).widget().setParent(None)

			# clear word inputs list
			self.word_inputs = []
			self.num_word_inputs_displayed = 1

			# create widget for first word
			first_word = QLineEdit()
			first_word.setPlaceholderText("...")
			self.next_placeholder_text = "+, -, or ="

			# connect to more input generator
			first_word.textEdited.connect(self.add_input_generator)

			# add word input to layout
			self.add_layout.addWidget(first_word)

			# add to list of word inputs
			self.word_inputs.append(first_word)

	def add_tab_collect_values(self):
		self.positive_words = []
		self.negative_words = []
		cur_sign = "+"

		for i in range(self.add_layout.count()):
			text = str(self.add_layout.itemAt(i).widget().text())
			if text=="=": break
			if text not in ["+","-"]:
				if cur_sign=="+": self.positive_words.append(text)
				if cur_sign=="-": self.negative_words.append(text)
				continue
			cur_sign = text

	def add_tab_get_result(self):
		self.add_result.setText("...")
		self.sum_worker = wikilearn_worker(parent=self)
		self.sum_worker.job = "algebra"
		self.sum_worker.positive_words = self.positive_words
		self.sum_worker.negative_words = self.negative_words
		self.sum_worker.text_encoder   = self.text_encoder
		self.sum_worker.start()

	def got_sum(self):
		self.add_result.setText(self.sum_worker.output)

	def add_input_generator(self):
		if len(self.word_inputs)==0: return

		if self.word_inputs[-1].hasFocus():

			if self.word_inputs[-1].text() in ["+","-","="]:
				txt = self.word_inputs[-1].text()
				self.add_layout.itemAt(len(self.word_inputs)-1).widget().setParent(None)
				self.add_layout.addWidget(QLabel(str(txt)))
				froze = True

				if txt=="=":
					self.add_tab_collect_values()
					return self.add_tab_get_result()
			else:
				froze = False

			'''
			if froze==False:
				if self.word_inputs[-1].text()[-1] in ["+","-"]:
					txt = self.word_inputs[-1].text()[-1]
					self.add_layout.addWidget(QLabel(str(txt)))
					froze = True
			'''

			new_word = QLineEdit()
			new_word.setPlaceholderText(self.next_placeholder_text)
			if self.next_placeholder_text=="+, -, or =":
				self.next_placeholder_text=="..."
			else:
				self.next_placeholder_text=="+, -, or ="

			new_word.textChanged.connect(self.add_input_generator)
			self.add_layout.addWidget(new_word)
			self.word_inputs.append(new_word)

			if froze:
				new_word.setFocus()

	def collect_values(self):
		self.query_1 = str(self.path_query_1.text())
		self.query_2 = str(self.path_query_2.text())
		try:
			self.cost = int(str(self.path_cost_input.text()))
		except:
			self.cost = None
		try:
			self.branching_factor = int(str(self.path_branching_factor_input.text()))
		except:
			self.branching_factor = None

	def path_query_changed(self):
		self.collect_values()

		if self.query_1 in [" ",""]: return
		if self.query_2 in [" ",""]: return
		if self.branching_factor==None or self.cost==None: return

		self.close_workers()

		new_worker                  = wikilearn_worker(parent=self)
		new_worker.start_query      = self.query_1
		new_worker.end_query        = self.query_2
		new_worker.branching_factor = self.branching_factor
		new_worker.weight           = self.cost
		new_worker.job 				= "path"
		new_worker.encoder          = self.text_encoder
		new_worker.start()

		self.workers.append(new_worker)

	def got_path(self):
		for f in self.workers:
			if f.job=="path":
				if f.valid:
					f.valid   = False
					soln_path = f.solution_path
					self.path_result_widget.clear()
					for word in reversed(soln_path):
						self.path_result_widget.append(word)
					del self.workers[self.workers.index(f)]
					return

	def no_path(self):
		self.path_result_widget.clear()

	def open_window(self):
		self.show()
		sleep(0.1)
		if not self.init_vars(): self.hide()

class exit_dialog(QWidget):
	exit_ok       = pyqtSignal()
	exit_canceled = pyqtSignal()

	def __init__(self,parent=None):
		super(exit_dialog,self).__init__()
		self.parent = parent
		self.connect(self,SIGNAL("exit_ok()"),self.parent.exit_accepted)
		self.connect(self,SIGNAL("exit_canceled()"),self.parent.exit_canceled)
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle("Exit Dialog")
		self.layout = QVBoxLayout(self)

		self.label = QLabel()
		self.layout.addWidget(self.label)

		self.button_row = QHBoxLayout()
		self.cancel_button = QPushButton("Cancel")
		self.cancel_button.clicked.connect(self.cancel_pressed)

		self.ok_button = QPushButton("Ok")
		self.ok_button.clicked.connect(self.ok_pressed)

		self.button_row.addWidget(self.cancel_button)
		self.button_row.addWidget(self.ok_button)

		self.layout.addLayout(self.button_row)

	def open_window(self,message,location):
		self.move(location)
		self.resize(self.sizeHint())
		self.label.setText(message)
		self.show()

	def cancel_pressed(self):
		self.hide()
		self.exit_canceled.emit()

	def ok_pressed(self):
		self.hide()
		self.exit_ok.emit()

	def closeEvent(self,e):
		self.cancel_pressed()

class main_menu(QWidget):

	def __init__(self,parent=None):
		super(main_menu,self).__init__()
		self.notification_gui 	= notification_window(parent=self)
		self.exit_gui 			= exit_dialog(parent=self)
		self.wikiserver_gui 	= wikiserver_window(parent=self)
		self.wikiparse_gui 		= wikiparse_window(parent=self)
		self.wikilearn_gui 		= wikilearn_window(parent=self)
		self.init_ui()

	def init_ui(self):
		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Control Panel")

		p = self.palette()
		p.setColor(self.backgroundRole(),QColor(255,255,255))
		self.setPalette(p)

		self.toolbar = QMenuBar(self)
		self.toolbar.setFixedWidth(390)

		file_menu = self.toolbar.addMenu("File")
		file_menu.addAction("Quit",self.quit,QKeySequence("Ctrl+Q"))

		tools_menu = self.toolbar.addMenu("Tools")

		tools_menu.addAction("WikiServer",self.open_wikiserver,QKeySequence("Ctrl+1"))
		self.wikiparse_menu_item = tools_menu.addAction("WikiParse",self.open_wikiparse,QKeySequence("Ctrl+2"))
		tools_menu.addAction("WikiLearn",self.open_wikilearn,QKeySequence("Ctrl+3"))

		tools_menu.addSeparator()
		self.cancel_parsing_action = tools_menu.addAction("Cancel Parsing",self.cancel_parsing)
		self.cancel_parsing_action.setEnabled(False)

		help_menu = self.toolbar.addMenu("Help")
		help_menu.addAction("WikiClassify 2.0",self.open_repo)

		if sys.platform!="darwin": self.layout.addSpacing(20)

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

		wikiserver_row.addWidget(self.wikiserver_button)
		wikiparse_row.addWidget(self.wikiparse_button)
		wikilearn_row.addWidget(self.wikilearn_button)

		wikiserver_row.addStretch()
		wikiparse_row.addStretch()
		wikilearn_row.addStretch()

		self.wikilearn_button.clicked.connect(self.open_wikilearn)
		self.wikiparse_button.clicked.connect(self.open_wikiparse)
		self.wikiserver_button.clicked.connect(self.open_wikiserver)

		#self.layout.addSpacing(10)
		self.layout.addLayout(wikiserver_row)
		self.layout.addLayout(wikiparse_row)
		self.layout.addLayout(wikilearn_row)
		self.layout.addSpacing(10)

		self.setFixedWidth(370)
		self.setFixedHeight(410)
		if sys.platform =="darwin": self.setFixedHeight(500)
		else: self.setFixedHeight(435)
		#if sys.platform =="win32": self.setFixedHeight(435)

		framegm = self.frameGeometry()
		screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
		centerpt = QApplication.desktop().screenGeometry(screen).center()
		framegm.moveCenter(centerpt)
		self.move(framegm.topLeft())

		self.show()

	def open_repo(self):
		webbrowser.open("http://www.github.com/bfaure/WikiClassify2.0")

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
		self.hide()
		self.wikilearn_gui.open_window()

	def closeEvent(self,e):
		self.quit()

	def quit(self):
		if not self.wikiparse_button.isEnabled():
			global_point = self.mapToGlobal(self.rect().topLeft())
			self.exit_gui.open_window("Still parsing, want to exit?",global_point)
			return
		sys.exit(1)

	def exit_accepted(self):
		if not self.wikiparse_button.isEnabled(): self.cancel_parsing()
		sys.exit(1)

	def exit_canceled(self):
		self.show()

	def done_parsing(self):
		self.wikiparse_button.setEnabled(True)
		self.wikiparse_menu_item.setEnabled(True)
		self.cancel_parsing_action.setEnabled(False)
		global_point = self.mapToGlobal(self.rect().topLeft())
		self.notification_gui.set_notification("Parsing is complete",global_point)

	def parsing_started(self):
		self.wikiparse_gui.hide()
		self.wikiparse_button.setEnabled(False)
		self.wikiparse_menu_item.setEnabled(False)
		self.cancel_parsing_action.setEnabled(True)
		self.show()
		global_point = self.mapToGlobal(self.rect().topLeft())
		self.notification_gui.set_notification("Parsing has begun, see command line for detail",global_point)

	def cancel_parsing(self):
		self.wikiparse_gui.worker.terminate()

		process_name = "wikiparse.out"
		for proc in psutil.process_iter():
			if proc.name()==process_name: proc.kill()

		self.wikiparse_button.setEnabled(True)
		self.wikiparse_menu_item.setEnabled(True)
		self.cancel_parsing_action.setEnabled(False)
		global_point = self.mapToGlobal(self.rect().topLeft())
		self.notification_gui.set_notification("Parsing canceled",global_point)
		print("\nParsing canceled.\n")

def start_gui():
	global main_menu_window
	app              = QApplication(sys.argv)
	app.setStyle('plastique')
	main_menu_window = main_menu(app)
	print("Opened GUI Window.\n")
	sys.exit(app.exec_())
