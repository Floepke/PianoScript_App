

def script_1_How_to_start_scripting(script):

    text = '''Welcome to the first tutorial on how to write scripts for PianoScript.
    In filepath "USERNAME/.pianoscript/" are the configuration files of PianoScript. 
    Don't touch them but in the "USERNAME/.pianoscript/pianoscripts/" folder you 
    can create your own script.py file and write your own scripts to manipulate the
    .pianoscript files in your own way. in that directory you can find "tutorial.py".
    
    You can follow this tutorial by reading the code and comments. In the Scripts 
    menu from PianoScript you can run every tutorial script by looking in the 
    Tutorials menu.'''

    # This function (That comes from the Script class in the source code) creates 
    # the info popup showing the above text.
    script.info(message=text)


def script_2_How_it_works(script):

    text = '''In your scripts.py file, every function name that you want to call from within
    PianoScript starts with "script_" folowed by the function name. The function name is 
    displayed in the script menu as soon as you save it and the python code has no wrong syntax.
    
    The scripts get's called from within PianoScript and it's given a parameter we call "script".
    "script" is an instance of the Script() class from the source code. The Script() class contains
    handy functions (that are listed more below) and really impartant: the score file you edit with
    PianoScript in the form of a dictionary.'''

    # example of a warning message popup
    script.warning(message=text)


def script_3_User_input_for_scripts(script):

    text = '''This is a user input ask_str() dialog. From now on follow the tutorial
    further using a text editor (like vscode or sublime text) and open 
    "USERNAME/.pianoscript/pianoscripts/tutorial.py"'''

    user_input = script.ask_str(message=text)

    if user_input.isdigit():
        # user_input can be converted to an int
        user_input = int(user_input)
        script.score['properties']['page_height'] = user_input
        script.error(f'''The script changed the page height of the document to {user_input} mm. 
                     (You can hit ctl/cmd+z to change it back)''')
    else:
        script.score['header']['title'] = user_input
        script.info(f'''This script changed the title of the current header title to "{user_input}".''')


def script_4_Script_template(script):
    text = f'''If you want you can now create your first script by creating: 
    "USERNAME/.pianoscript/pianoscripts/myscript.py"and write your own script 
    by copying the {script_4_Script_template.__name__}() function to your
    myscript.py file.
    Run the script using menu Scripts>User>4 Script template.'''

    script.info(text)

    text = '''This script is showing some examples of what you can do with scripts.
    A list of all available functions you can call from "script":'''

    list_of_available_functions = [
        (script.ask_str, 'asks for a string and returns user_input or None.'),
        (script.ask_int, 'asks for a int; returns int or None'),
        (script.ask_float, 'asks for a float; returns float or None'),
        (script.ask_yesno, 'asks for yes or no; returns True or False'),
        (script.ask_list, 'asks the user for a string and returns a tuple (chosen_value, chosen_index)')
    ]
    for available_functions in list_of_available_functions:
        available_functions[0](available_functions[1])

    