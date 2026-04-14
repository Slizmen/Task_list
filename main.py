import sys

from PyQt6.QtWidgets import QApplication, QWidget, QDialog, QInputDialog, QMessageBox, QListWidgetItem

import sqlite3

from categories_design import Ui_categories

from tasks_design import Ui_Form

from PyQt6.QtCore import Qt

NAME_DATABASE ='tasksList_db.db'

def createTables(con):
    try:
        with con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS categories(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                description TEXT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
                ON DELETE CASCADE
                ); 
            """)
    except sqlite3.DatabaseError as e:
        print(e)
        sys.exit(-1)

class Categories(QDialog, Ui_categories):
    def __init__(self, con):
        super().__init__()
        self.setupUi(self)
        self.con = con
        self.loadCategories()
        self.addCategoryButton.clicked.connect(self.addCategory)
        self.deleteCategoryButton.clicked.connect(self.deleteCategory)
    
    def loadCategories(self):
        categories = self.con.execute('SELECT * FROM categories;')
        self.categoriesList.clear()
        for i in categories:
            self.categoriesList.addItem(i[1])
    
    def addCategory(self):
        title, ok = QInputDialog.getText(self, 'Добавление категории', 'Введите название категории:')
        if ok:
                with self.con:
                    self.con.execute('''INSERT INTO categories(title) 
                                        VALUES(?);
                        ''', (title,))
        self.loadCategories()

    def deleteCategory(self):
        item = self.categoriesList.item(self.categoriesList.currentRow())
        title = item.text()
        categories_id = self.con.execute('''
                                    SELECT id From categories
                                    WHERE title = ?;''', (title,)).fetchone()[0]
        result =QMessageBox.question(self, 'Вы уверены?', f'Удаление категории {title}?')
        if result == QMessageBox.StandardButton.Yes:
            with self.con:
                self.con.execute('''
                                DELETE FROM categories
                                WHERE id = ?;
                                 ''', (categories_id,))
        self.loadCategories()
    
class Tasks(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect(f'file:{NAME_DATABASE}?mode=rw')
        createTables(self.con)
        self.con.execute('PRAGMA foreign_keys = 1')
        self.categoriesButton.clicked.connect(self.showCategories)
        self.addTaskButton.clicked.connect(self.addTask)
        self.tasksList.itemClicked.connect(self.taskDetail)
        self.deleteTaskButton.clicked.connect(self.deleteTask)
        self.filterCategory.currentTextChanged.connect(self.loadTasks)
        self.loadCategories()
        self.loadTasks()

    
    def loadTasks(self):
        tasks = self.con.execute('''SELECT tasks.id, tasks.title, description, done, categories.title
                                 FROM tasks 
                                 JOIN categories ON category_id == categories.id;''')
        self.tasksList.clear()
        for i in tasks:
            item = QListWidgetItem(i[1])
            item.setCheckState(Qt.CheckState.Checked if i[3] else Qt.CheckState.Unchecked)
            if self.filterCategory.currentText() == '':
                self.tasksList.addItem(item)
            else:
                if self.filterCategory.currentText() == i[4]:
                    self.tasksList.addItem(item)

    
    def showCategories(self):
        self.categories = Categories(self.con)
        self.categories.exec()
        self.loadTasks()
        self.loadCategories()
    
    def addTask(self):
        title = self.taskTitle.text()
        description = self.taskDescription.toPlainText()
        category = self.selectCategory.currentText()
        if not category:
            QMessageBox.critical(self, 'Добавьте категорию', 'Нельзя добавить задачу без категории')
            return
        category_id = self.con.execute('''SELECT id
                                        FROM categories
                                        WHERE title = ?;
                                       ''', (category,)).fetchone()[0]
        try:
            with self.con:
                self.con.execute('''INSERT INTO tasks(title, description, category_id)
                                 VALUES(?, ?, ?);''', (title, description, category_id))
        except sqlite3.DatabaseError as e:
            QMessageBox.critical(self, 'Ошибка', f'{e}')
        self.loadTasks()
    
    def loadCategories(self):
        categories = self.con.execute('''SELECT id, title
                                      FROM categories;
                                      ''')
        self.selectCategory.clear()
        self.filterCategory.clear()
        for i in categories:
            self.selectCategory.addItem(i[1])
            self.filterCategory.addItem(i[1])
    
    def taskDetail(self, item):
        title = item.text()
        task = self.con.execute('''SELECT tasks.id, tasks.title, description, done, categories.title
                                FROM tasks
                                LEFT JOIN categories ON category_id == categories.id
                                WHERE tasks.title = ?;''', (title,)).fetchone()
        done = 1 if item.checkState() == Qt.CheckState.Checked else 0
        with self.con:
            self.con.execute('''UPDATE tasks
                             SET done = ?
                             WHERE id = ?;''', (done, task[0]))
        self.taskTitle.setText(task[1])
        self.taskDescription.setText(task[2])
        self.selectCategory.setCurrentText(task[4])
    
    def deleteTask(self):
        item = self.tasksList.item(self.tasksList.currentRow())
        if not item:
            QMessageBox.warning(self, 'Выберите задачу', 'Необходимо выбрать задачу')
            return
        title = item.text()
        task_id = self.con.execute('''SELECT id
                                   FROM tasks
                                   WHERE title = ?;''', (title,)).fetchone()[0]
        result = QMessageBox.question(self, 'Вы уверены?', f'Удалить задачу {title}?')
        if result == QMessageBox.StandardButton.Yes:
            with self.con:
                self.con.execute('''DELETE FROM tasks
                                 WHERE id = ?;''', (task_id,))
        self.loadTasks()

app = QApplication(sys.argv)
window = Tasks()
window.show()
sys.exit(app.exec())



