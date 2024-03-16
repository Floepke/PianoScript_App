import os
import importlib.util
import inspect
import traceback
from PySide6.QtGui import QAction


class LoadScripts:

    def __init__(self, io):
        self.io = io
        self.factory_directory = 'imports/scripting/factory_scripts/'

        # Load the scripts from the user directory
        self.user_directory = os.path.expanduser('~/.pianoscript/pianoscripts/')
        if not os.path.exists(self.user_directory):
            os.makedirs(self.user_directory)
        self.script_menu = io['gui'].pianoscripts_menu

        factory_menu = self.script_menu.addMenu('Factory')
        self.load(self.factory_directory, factory_menu)

        # Load the scripts from the user directory if there are any
        user_menu = self.script_menu.addMenu('User')
        self.load(self.user_directory, user_menu)

    def build_menu(self, menu):
        for name in os.listdir(self.user_directory):
            if name == '__pycache__':
                continue
            path = os.path.join(self.user_directory, name)
            if os.path.isdir(path):
                submenu = menu.addMenu(name)
                self.build_menu(submenu)

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
                    action = QAction('⚙ ' + func_name, menu)
                    action.triggered.connect(lambda func=func, module=module: self.eval_func(func, module))
                    menu.addAction(action)

    def eval_func(self, func, module):
        try:
            func(self.io)
            print(f'Script "{module.__name__}" executed successfully')
            self.io['maineditor'].update('page_change')
            self.io['maineditor'].redraw_editor()
        except Exception as e:
            print(f'-------------ERROR IN SCRIPT "{module.__name__}"-----------------')
            traceback.print_exc()
            print('---------------------------------------------------------------')