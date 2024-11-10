# _includes/file_handling.py
import os
import inquirer
from loguru import logger

def get_proxy_ip(proxy_url):
    return proxy_url.split("://")[1].split(":")[0]

def get_proxy_name(proxy_url):
    proxy_ip = get_proxy_ip(proxy_url)
    return proxy_ip[:15]

def update_file(file_path, content, action="add"):
    if action == "add":
        if not os.path.exists(file_path):
            with open(file_path, 'w'):  # Create file if it doesn't exist
                pass
        with open(file_path, 'r+') as file:
            lines = file.read().splitlines()
            if content not in lines:
                file.write(content + "\n")
    elif action == "remove":
        with open(file_path, 'r') as file:
            lines = file.readlines()
        with open(file_path, 'w') as file:
            for line in lines:
                if line.strip() != content:
                    file.write(line)

def load_proxies():
    proxy_files = [f for f in os.listdir() if f.startswith('proxies_') and f.endswith('.txt')]

    if not proxy_files:
        logger.error("No proxy files with prefix 'proxies_' found.")
        return None, None  # Return None for both

    spaced_choices = ["               Add All"] + [f"               {file}" for file in proxy_files]

    questions = [
        inquirer.List('selected_file',
                      message="        Select a proxy file",
                      choices=spaced_choices)
    ]
    answers = inquirer.prompt(questions)

    if answers is None or 'selected_file' not in answers:
        logger.error("No file selected. Exiting.\n")
        return None, None  # Return None for both

    selected_file = answers['selected_file'].strip()
    if selected_file == "Add All":
        local_proxies = []
        for file_name in proxy_files:
            with open(file_name, 'r') as file:
                local_proxies.extend(file.read().splitlines())
        selected_file_display = "All proxy files"
    else:
        with open(selected_file, 'r') as file:
            local_proxies = file.read().splitlines()
        selected_file_display = selected_file

    return local_proxies, selected_file_display