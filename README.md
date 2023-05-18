# gpt-commit-messages

## About

Command that has GPT4 draft commit messages for me.

Also looks for errors in diff.


## Installation

### Prerequisites

System must have Python3

### Steps

1. Install Poetry via `pip install poetry`
2. Clone `git clone https://github.com/ninjaa/gpt-commit-messages.git`
3. cd into `gpt-commit-messages` directory
4. Run `poetry install` in that folder
5. Add OPENAI*API_KEY to your bashrc, il.e `export OPENAI_API_KEY="sk*\*"`
6. Add following alias to your bashrc
   `alias gpt_commit='poetry run python /path/to/your/script/main.py'`

### Example usage

```
ninjaa@8MeetsFate:~/gpt-commit-messages$ gcm
There are uncommitted changes
.M README.md
 M gcm
 M gpt_commit_messages/gpt_commit_messages.py
Do you want to add them? [y/N]: y
Getting commit message from OpenAI.
Commit message:

feat: Add example usage and improve uncommitted changes handling

- Added example usage section in README.md
- Moved uncommitted changes check to the beginning of the `generate_commit_message` function
- Removed redundant newline and commented code


Checking for errors using GPT4.
Potential issues found:

I found the following issues in the code diffs:

...

Overall, the changes improve the code organization and functionality.

Commit? [y/N]: y
[main 6d492b7] feat: Add example usage and improve uncommitted changes handling
 3 files changed, 11 insertions(+), 8 deletions(-)

Push? [y/N]: y
Enumerating objects: 11, done.
Counting objects: 100% (11/11), done.
Delta compression using up to 8 threads
Compressing objects: 100% (6/6), done.
Writing objects: 100% (6/6), 740 bytes | 740.00 KiB/s, done.
Total 6 (delta 4), reused 0 (delta 0)
remote: Resolving deltas: 100% (4/4), completed with 4 local objects.
To github.com:ninjaa/gpt-commit-messages.git
   5ccf1ba..6d492b7  main -> main
```

## License

MIT

## Author

Aditya Advani
