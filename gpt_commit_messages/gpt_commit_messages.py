import click
import openai
import os
import subprocess


def get_openai_response(prompt, error_check=False):
    if error_check:
        system_prompt = "This assistant checks for potential issues in code changes. Please find the issues in the following code diffs."
    else:
        system_prompt = "This is a code revision assistant. It's tasked to create commit messages from code diffs."

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


def get_diffs(repo_path):
    process = subprocess.run(['git', '-C', repo_path, 'diff', 'HEAD'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    diffs = process.stdout

    if len(diffs) > 6000:
        click.echo("Diff is too large, truncating.", err=True)
        diffs = diffs[:6000]

    return diffs


def generate_commit_prompt(repo_path):
    diffs = get_diffs(repo_path)
    prompt = "I have a code change with the following diffs:\n"
    prompt += diffs
    prompt += "\nWhat should be the commit message for this change? Please categorize the commit type as one of the following: [build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test]. The first line of the commit message should be of the format <commit type>: <commit message>, where the length of commit_message should be no more than 50 characters. Feel free to add a few more bullet points with more details if relevant. Put a newline between the short message and the details."

    return prompt


def generate_error_prompt(repo_path):
    diffs = get_diffs(repo_path)
    return "Please find errors or significant design flaws in the following code diffs:\n" + diffs + \
        "\nBe succint and don't mention generic tips like recommending adding comments. If errors are found, please suggest a fix along with code for the fix. Mention line numbers etc where things are found. Succintness++ ty ty. Do not draft a commit message. Return blank if nothing notable is found."


@click.group(invoke_without_command=True)
@click.option('--commit', is_flag=True)
@click.option('--push', is_flag=True)
@click.pass_context
def cli(ctx, commit, push):
    ctx.ensure_object(dict)
    ctx.obj['COMMIT'] = commit
    ctx.obj['PUSH'] = push
    if ctx.invoked_subcommand is None:
        ctx.invoke(generate_commit_message)


@click.command()
@click.argument('repo_path', type=click.Path(exists=True), default=os.getcwd())
def print_prompt(repo_path):
    click.echo(generate_commit_prompt(repo_path))


@click.command()
@click.argument('repo_path', type=click.Path(exists=True), default=os.getcwd())
@click.pass_context
def generate_commit_message(ctx, repo_path):
    # Check if there are uncommitted changes
    git_status = subprocess.run(['git', '-C', repo_path, 'status',
                                '--porcelain'], capture_output=True, text=True).stdout.strip()
    if git_status and click.confirm(f'There are uncommitted changes\n.{git_status}\nDo you want to add them?'):
        subprocess.run(['git', '-C', repo_path, 'add', '-A'], check=True)

    commit = ctx.obj.get('COMMIT', False)
    push = ctx.obj.get('PUSH', False)

    prompt = generate_commit_prompt(repo_path)
    click.echo("Getting commit message from OpenAI.")
    commit_message = get_openai_response(prompt).strip()

    click.echo("Commit message:\n")
    click.echo(commit_message)
    click.echo("\n")

    error_prompt = generate_error_prompt(repo_path)
    click.echo("Checking for errors using GPT4.")
    error_message = get_openai_response(error_prompt, error_check=True)

    if error_message.strip():
        click.echo("Potential issues found:\n", err=True)
        click.echo(error_message, err=True)

    committed = False
    if commit or click.confirm('Commit?'):
        subprocess.run(['git', '-C', repo_path, 'commit',
                       '-m', commit_message], check=True)
        committed = True

    if committed and (push or click.confirm('Push?')):
        subprocess.run(['git', '-C', repo_path, 'push'], check=True)


cli.add_command(print_prompt)
cli.add_command(generate_commit_message)

if __name__ == "__main__":
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key is None:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    openai.api_key = openai_api_key
    cli()
