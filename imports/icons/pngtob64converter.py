import os
import base64

script_directory = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_directory, 'icons.py')
iconloader_file = os.path.join(script_directory, 'iconloader.py')

with open(output_file, 'w') as f:
    for filename in os.listdir(script_directory):
        if filename.endswith('.png'):
            filepath = os.path.join(script_directory, filename)
            with open(filepath, 'rb') as img_file:
                img_bytes = img_file.read()
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                variable_name = filename.replace('.png', '').upper() + '_B64'
                f.write('{} = "{}"\n'.format(variable_name, img_b64))
                print(f"Written base64 string for {filename} to icons.py")

    # Append the content of iconloader.py to icons.py
    with open(iconloader_file, 'r') as iconloader:
        f.write('\n' + iconloader.read())
        print("Appended content of iconloader.py to icons.py")

print("Base64 strings and iconloader.py content written to icons.py")