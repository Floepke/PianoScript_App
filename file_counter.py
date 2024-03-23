import os

def count_lines_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines_with_content = [line for line in file if line.strip()]
        return len(lines_with_content)

def count_lines_in_directory(directory, kinds):
    total_lines = 0
    total_files = 0  # Add a file counter
    for root, _, files in os.walk(directory):
        for file in files:
            for k in kinds:
                filelines = 0
                if file.endswith(f'.{k}'):
                    try: 
                        c = count_lines_in_file(os.path.join(root, file))
                    except: 
                        continue
                    total_lines += c
                    filelines += c
                    total_files += 1  # Increment the file counter
                    print(f'file: {file} | Lines: {filelines}')
    return total_lines, total_files  # Return the file counter as well

def main(root_directory, kinds):
    total_lines, total_files = count_lines_in_directory(root_directory, kinds)  # Unpack the returned tuple
    print(f"Total lines in all {kinds} files: {total_lines}")
    print(f"Total number of {kinds} files: {total_files}")  # Print the total number of files

if __name__ == "__main__":
    root_directory = ""  # Change this to the desired root directory
    kinds = ".py".split()
    main(root_directory, kinds)