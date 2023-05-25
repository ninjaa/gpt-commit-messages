import click
import concurrent.futures
import openai
import os
import subprocess

from lib.count_tokens import count_tokens, encode_tokens, decode_tokens


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


def get_staged_diffs(repo_path):
    process = subprocess.run(['git', '-C', repo_path, 'diff', 'HEAD', '--staged'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    diffs = process.stdout

    num_tokens = count_tokens(diffs)

    if num_tokens > 3000:
        click.echo(
            f"Diff at {len(diffs)} chars, {num_tokens} tokens is too large, truncating.", err=True)
        tokens = encode_tokens(diffs)
        diffs = decode_tokens(tokens[:3000])

    return diffs


def generate_commit_prompt(repo_path):
    diffs = get_staged_diffs(repo_path)
    prompt = "I have a code change with the following diffs:\n"
    prompt += diffs
    prompt += "\nWhat should be the commit message for this change? Please categorize the commit type as one of the following: [build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test]. The first line of the commit message should be of the format <commit type>: <commit message>, where the length of commit_message should be no more than 50 characters. Feel free to add a few more bullet points with more details if relevant. Put a newline between the short message and the details."

    return prompt


def generate_error_prompt(repo_path):
    diffs = get_staged_diffs(repo_path)
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


def commit_or_edit(repo_path, commit_message, force_commit=False):

    if force_commit:
        click.echo('Committing changes...')
        # commit the changes here
        subprocess.run(['git', '-C', repo_path, 'commit',
                       '-m', commit_message], check=True)
        return True

    option = click.prompt(
        'Do you want to commit changes? (y/n/e for edit)', type=str)
    if option.lower() == 'y':
        click.echo('Committing changes...')
        # commit the changes here
        subprocess.run(['git', '-C', repo_path, 'commit',
                       '-m', commit_message], check=True)
        return True
    elif option.lower() == 'e':
        click.echo('Editing changes...')
        # edit the changes here
        subprocess.run(['git', '-C', repo_path, 'commit',
                       '-e', '-m', commit_message], check=True)
        return True
    elif option.lower() == 'n':
        click.echo('Not committing changes.')
    else:
        click.echo('Invalid option')

    return False


@click.command()
@click.argument('repo_path', type=click.Path(exists=True), default=os.getcwd())
@click.pass_context
def generate_commit_message(ctx, repo_path):
    # Get the staged changes
    staged_changes = subprocess.run(['git', '-C', repo_path, 'diff', '--staged', '--name-only'],
                                    capture_output=True, text=True).stdout.strip()
    if staged_changes:
        click.echo(
            f'The following changes are staged for the next commit:\n{staged_changes}\n')

    # Get the unstaged changes
    unstaged_changes = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'],
                                      capture_output=True, text=True).stdout.strip()

    # Get the untracked files
    untracked_files = subprocess.run(['git', '-C', repo_path, 'ls-files', '--others', '--exclude-standard'],
                                     capture_output=True, text=True).stdout.strip()

    unstaged_and_untracked = "\n".join(
        [unstaged_changes, untracked_files]).strip()
    if unstaged_and_untracked:
        click.echo(
            f'The following changes are not staged for commit:\n{unstaged_and_untracked}\n')
        if click.confirm('Do you want to stage these changes?'):
            subprocess.run(['git', '-C', repo_path, 'add', '-A'], check=True)

    commit = ctx.obj.get('COMMIT', False)
    push = ctx.obj.get('PUSH', False)

    # get the commit message and error analysis from GPT4 both asynchronously at the same time
    with concurrent.futures.ThreadPoolExecutor() as executor:
        prompt = generate_commit_prompt(repo_path)
        error_prompt = generate_error_prompt(repo_path)

        future_to_message = {
            executor.submit(get_openai_response, prompt): "commit",
            executor.submit(get_openai_response, error_prompt, error_check=True): "error",
        }

        for future in concurrent.futures.as_completed(future_to_message):
            msg_type = future_to_message[future]
            try:
                data = future.result()
            except Exception as exc:
                click.echo(
                    f'{msg_type} generated an exception: {exc}\n', err=True)
            else:
                if msg_type == "commit":
                    commit_message = data.strip()
                    click.echo("Commit message:\n")
                    click.echo(commit_message)
                    click.echo("\n")
                else:
                    error_message = data.strip()
                    if error_message:
                        click.echo("Potential issues found:\n", err=True)
                        click.echo(error_message, err=True)

    committed = commit_or_edit(repo_path, commit_message, commit)

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
