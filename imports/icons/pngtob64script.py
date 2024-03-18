import os
from base64 import encodebytes as encode_b64

def pict_as_str(filename: str) -> str:
    """ convert an image to string """

    buffer = open(filename, 'rb').read()
    result = encode_b64(buffer).decode('utf8')
    return str(result)

script_directory = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_directory, 'icons.py')
iconloader_file = os.path.join(script_directory, 'iconblueprint.py')

with open(output_file, 'w') as f:
    for filename in os.listdir(script_directory):
        if filename.endswith('.png'):
            filepath = os.path.join(script_directory, filename)
            with open(filepath, 'rb') as img_file:
                img_bytes = img_file.read()
                img_b64 = pict_as_str(filepath)
                variable_name = filename.replace('.png', '').upper() + '_B64'
                f.write('{} = """{}"""\n'.format(variable_name, img_b64))
                print(f"Written base64 string for {filename} to icons.py")

    # Append the content of iconblueprint.py to icons.py
    with open(iconloader_file, 'r') as iconblueprint:
        f.write('\n' + iconblueprint.read())
        print("Appended content of iconblueprint.py to icons.py")

print("Base64 strings and iconblueprint.py content written to icons.py")
