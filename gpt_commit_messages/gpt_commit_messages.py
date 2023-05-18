import click
import openai
import os
import subprocess
from enum import Enum

openai.api_key = os.getenv('OPENAI_API_KEY')

SYSTEM_PROMPT = "This is a code revision assistant. It's tasked to create commit messages from code diffs."


class CommitType(Enum):
    BUILD = "build"
    CHORE = "chore"
    CI = "ci"
    DOCS = "docs"
    FEAT = "feat"
    FIX = "fix"
    PERF = "perf"
    REFACTOR = "refactor"
    REVERT = "revert"
    STYLE = "style"
    TEST = "test"


def get_openai_response(prompt, error_check=False):
    if error_check:
        system_prompt = "This assistant checks for potential issues in code changes. Please find the issues in the following code diffs."
    else:
        system_prompt = SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2000,
        temperature=0.7,
    )

    return response.choices[0].message["content"]


def generate_prompt(repo_path):
    process = subprocess.run(['git', '-C', repo_path, 'diff', 'HEAD'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    diffs = process.stdout

    if len(diffs) > 6000:
        click.echo("Diff is too large, truncating.", err=True)
        diffs = diffs[:6000]

    prompt = "I have a code change with the following diffs:\n"
    prompt += diffs
    prompt += "\nWhat should be the commit message for this change? Please categorize the commit type as one of the following: [build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test]. The first line of the commit message should be of the format <commit type>: <commit message>, where the length of commit_message should be no more than 50 characters."

    return prompt


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(generate_commit_message)


@click.command()
@click.argument('repo_path', type=click.Path(exists=True), default=os.getcwd())
def print_prompt(repo_path):
    click.echo(generate_prompt(repo_path))


@click.command()
@click.argument('repo_path', type=click.Path(exists=True), default=os.getcwd())
@click.option('--commit', is_flag=True)
def generate_commit_message(repo_path, commit):
    prompt = generate_prompt(repo_path)
    response = get_openai_response(prompt).strip()

    click.echo(response)
    # commit_message = response

    # prompt_error = "Please find the errors or design flaws in the following code diffs:\n" + prompt
    # error_message = get_openai_response(prompt_error, error_check=True)

    # if error_message.strip():
    #     click.echo("Potential issues found:\n", err=True)
    #     click.echo(error_message, err=True)

    # click.echo(commit_message)

    # if commit:
    #     subprocess.run(['git', '-C', repo_path, 'commit',
    #                    '-m', commit_message], check=True)


cli.add_command(print_prompt)
cli.add_command(generate_commit_message)

if __name__ == "__main__":
    cli()
