import os
import importlib.util
import inspect
import traceback
import random
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QMenu
from imports.scripting.script import Script


class LoadScripts:
    '''
    Loads scripts from the factory and user directories and adds them to the menu
    '''

    def __init__(self, io):
        self.io = io
        self.factory_directory = 'imports/scripting/factory_scripts/'
        self.script = Script(io)

        # Load the scripts from the user directory
        self.user_directory = os.path.expanduser('~/.pianoscript/pianoscripts/')
        if not os.path.exists(self.user_directory):
            os.makedirs(self.user_directory)
        self.script_menu = io['gui'].pianoscripts_menu

        # run the menu building function on the script menu
        self.script_menu.aboutToShow.connect(lambda: self.build_menu(self.script_menu))

    def build_menu(self, menu):
        # empty the menu
        menu.clear()

        # Load the scripts from the factory directory
        factory_menu = SubMenu('Factory  ', self.script_menu)
        self.load(self.factory_directory, factory_menu)
        self.script_menu.addMenu(factory_menu)

        # Load the scripts from the user directory if there are any
        user_menu = SubMenu('User  ', self.script_menu)
        self.load(self.user_directory, user_menu)
        self.script_menu.addMenu(user_menu)

    def load(self, directory=None, menu=None):
        if directory is None:
            directory = self.factory_directory
        if menu is None:
            menu = self.script_menu

        for name in os.listdir(directory):
            if name == '__pycache__':
                continue

            path = os.path.join(directory, name)
            if os.path.isdir(path):
                submenu = menu.addMenu(name)
                self.load(path, submenu)
            elif name.endswith('.py'):
                script_name = name[:-3]  # remove .py extension
                spec = importlib.util.spec_from_file_location(script_name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for func_name, func in inspect.getmembers(module, inspect.isfunction):
                    if not func_name.startswith('script_'):
                        continue
                    action = QAction('⚙ ' + func_name[7:].replace('_', ' '), menu)
                    action.triggered.connect(lambda func=func, module=module: self.eval_func(func, module))
                    menu.addAction(action)

    def eval_func(self, func, module):
        try:
            self.io['script_name'] = 'Script: ' + func.__name__[7:].replace('_', ' ')
            func(self.script)
            print(f'Script "{func.__name__}" executed successfully')
            self.io['maineditor'].update('page_change')
            self.io['maineditor'].redraw_editor()
        except Exception as e:
            print(f'-------------ERROR IN SCRIPT "{func.__name__}"-----------------')
            traceback.print_exc()
            print('---------------------------------------------------------------')


class SubMenu(QMenu):
    ''' 
    A little customized QMenu with advanced color system 
    '''
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.offset = 5
        complementary_color = QColor.fromHsv(
            random.randint(0, 255), 25, 200)
        self.color1 = complementary_color.name()
        # negative color self.color2
        negative_color = QColor(self.color1).rgb() ^ 0xFFFFFF
        self.color2 = QColor(negative_color).name()
        self.b_color = 'black'
        self.color = 'white'
        self.setStyleSheet(f'background-color: {self.color1}; color: {self.color2};')
    
    def showEvent(self, event):
        super().showEvent(event)
        pos = self.pos()
        self.move(pos.x() + self.offset, pos.y())

    def addMenu(self, title):
        submenu = SubMenu(title + '  ', self)
        super().addMenu(submenu)
        return submenu