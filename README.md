# gpt-commit-messages
Command that has GPT3 draft commit messages for me

## Installation

### Prerequisites

System must have Python3

### Steps

1. Install Poetry via `pip install poetry`
2. Clone `git clone https://github.com/ninjaa/gpt-commit-messages.git`
3. cd into `gpt-commit-messages` directory
4. Run `poetry install` in that folder
5. Add OPENAI_API_KEY to your bashrc, il.e `export OPENAI_API_KEY="sk_*"`
6. Add following alias to your bashrc
`alias gpt_commit='poetry run python /path/to/your/script/main.py'`



