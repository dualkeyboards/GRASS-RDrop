# _includes/accounts_manager.py
import inquirer
from loguru import logger


def load_accounts():
    account_file = 'accounts.txt'
    try:
        with open(account_file, 'r') as f:
            accounts = [line.strip().split(",") for line in f if line.strip()]
            return accounts
    except FileNotFoundError:
        logger.error(f"Account file '{account_file}' not found. Please create the file with account entries.")
        return None

def select_account(accounts):
    if not accounts:
        logger.error("No accounts found in accounts.txt.")
        return None, None

    account_choices = {f"               {user_name}": _user_id for _user_id, user_name in accounts}

    account_question = [
        inquirer.List('selected_account',
                      message="        Select an account",
                      choices=list(account_choices.keys()))
    ]
    account_answer = inquirer.prompt(account_question)

    if account_answer is None or 'selected_account' not in account_answer:
        logger.error("No account selected. Exiting.\n")
        return None, None

    selected_user_name = account_answer['selected_account'].strip()
    _user_id = account_choices[f"               {selected_user_name}"]

    return selected_user_name, _user_id