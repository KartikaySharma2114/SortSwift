import os
import shutil
import subprocess
import tempfile
from tempfile import mkdtemp

try:
    from PIL import Image
except ImportError:
    print('Error: You need to install the "PIL" package. Type the following:')
    print('pip install pillow')

try:
    import pytesseract
except ImportError:
    print('Error: You need to install the "pytesseract" package. Type the following:')
    print('pip install pytesseract')
    exit()

try:
    from pdf2image import convert_from_path
except ImportError:
    print('Error: You need to install the "pdf2image" package. Type the following:')
    print('pip install pdf2image')
    exit()

import sys


def show_progress(progress):
    bar_length = 10
    status = ""
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "\r\n"
    block = int(round(bar_length * progress))
    progress_text = "\rPercent: [{0}] {1}% {2}".format(
        "#" * block + "-" * (bar_length - block), progress * 100, status)
    sys.stdout.write(progress_text)
    sys.stdout.flush()


def execute_command(command_args):
    try:
        result = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise FileNotFoundError(f"Command not found: {command_args[0]}")
    stdout, stderr = result.communicate()
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with return code {result.returncode}: {stderr.decode().strip()}")
    return stdout, stderr


def extract_text_from_pdf(pdf_path):
    temp_directory = mkdtemp()
    base_filename = os.path.join(temp_directory, 'page')
    extracted_texts = []
    try:
        execute_command(['pdftoppm', pdf_path, base_filename])
        for image_file in sorted(os.listdir(temp_directory)):
            image_path = os.path.join(temp_directory, image_file)
            text_content = pytesseract.image_to_string(Image.open(image_path))
            extracted_texts.append(text_content)
        return ''.join(extracted_texts)
    finally:
        shutil.rmtree(temp_directory)


def convert_pdf_to_text_recursively(src_dir, dest_dir, converted_count):
    total_pdfs = sum([len(files) for _, _, files in os.walk(src_dir) if any(file.lower().endswith('.pdf') for file in files)])
    for dirpath, _, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                relative_path = os.path.relpath(dirpath, src_dir)
                source_path = os.path.join(dirpath, file)
                output_directory = os.path.join(dest_dir, relative_path)
                output_file = os.path.join(output_directory, os.path.splitext(file)[0] + '.txt')
                if not os.path.exists(output_directory):
                    os.makedirs(output_directory)
                converted_count = convert_single_pdf_to_text(source_path, output_file, converted_count, total_pdfs)
    return converted_count


def convert_single_pdf_to_text(pdf_file, txt_file, count, total_pdfs):
    text_content = extract_text_from_pdf(pdf_file)
    with open(txt_file, 'w', encoding='utf-8') as output_file:
        output_file.write(text_content)
    count += 1
    show_progress(count / total_pdfs)
    return count


def main():
    print('********************************')
    print('*** PDF to TXT file via OCR ***')
    print('********************************')

    current_directory = os.path.dirname(os.path.realpath(__file__))
    source_path = input(f'Source file or folder of PDF(s) [{current_directory}]: ').strip() or current_directory
    destination_path = input(f'Destination folder for TXT [{current_directory}]: ').strip() or current_directory

    if os.path.exists(source_path):
        file_count = 0
        if os.path.isdir(source_path):
            file_count = convert_pdf_to_text_recursively(source_path, destination_path, file_count)
        elif os.path.isfile(source_path) and source_path.lower().endswith('.pdf'):
            file_name = os.path.splitext(os.path.basename(source_path))[0]
            file_count = convert_single_pdf_to_text(source_path, os.path.join(destination_path, file_name + '.txt'), file_count, 1)
        file_plural = 'files' if file_count != 1 else 'file'
        print(f'\n{file_count} {file_plural} converted')
    else:
        print(f'The path {source_path} seems to be invalid')


if __name__ == '__main__':
    main()
