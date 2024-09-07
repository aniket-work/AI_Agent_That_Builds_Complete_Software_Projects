import os
import json
import logging
import click
import zipfile
import shutil
from coder_ai_agent import CoderAIAgent


@click.command()
@click.argument("task", required=False)
@click.option("--file", type=click.Path(exists=True), help="Path to a markdown file containing the task")
@click.option("--model", default="mistral-nemo", help="The model to use for the LLM")
@click.option(
    "--provider",
    default="ollama",
    type=click.Choice(["ollama", "openai", "claude"]),
    help="The LLM provider to use",
)
@click.option(
    "--zip", type=click.Path(), help="Path to save the zip file of the agent run"
)
def cli(
        task: str = None,
        file: str = None,
        model: str = "mistral-nemo",
        provider: str = "ollama",
        zip: str = None,
):
    """
    Run Nemo Agent tasks to create Python projects using uv and pytest.
    If no task is provided, it will prompt the user for input.
    """
    # Store the original working directory
    original_dir = os.getcwd()

    # Read task from file if provided
    if file:
        with open(file, 'r') as f:
            task = f.read().strip()
    elif not task:
        task = click.prompt("Please enter your task")

    nemo_agent = CoderAIAgent(task=task)
    nemo_agent.run_task()

    project_dir = nemo_agent.pwd

    if zip:
        # Ensure the zip file is created in the original directory
        zip_path = os.path.join(original_dir, zip)

        # Create a zip file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
        print(f"Project files have been zipped to: {zip_path}")

        # Delete the project directory
        shutil.rmtree(project_dir)
        print(f"Project directory {project_dir} has been deleted.")
    else:
        print(f"Task completed. Project files are in: {nemo_agent.pwd}")


if __name__ == "__main__":
    cli()