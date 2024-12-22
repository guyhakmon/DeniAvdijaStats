import os
import subprocess
from datetime import datetime

# Define the directory containing the reaction files
reaction_files_dir = "/c:/Users/guyHa/study/fun/DeniAvdijaStats/"

# Get the current date to find today's reaction file
today = datetime.now().strftime('%B_%d,_%Y')
reaction_file = f"reactions_{today}.txt"
reaction_file_path = os.path.join(reaction_files_dir, reaction_file)

# Check if the reaction file exists
if os.path.exists(reaction_file_path):
    # Change to the directory containing the reaction files
    os.chdir(reaction_files_dir)

    # Add the new reaction file to the Git staging area
    subprocess.run(["git", "add", reaction_file])

    # Commit the new reaction file
    commit_message = f"Add reactions for the game on {today}"
    subprocess.run(["git", "commit", "-m", commit_message])

    # Push the changes to the remote repository
    subprocess.run(["git", "push", "origin", "main"])
else:
    print(f"No reaction file found for today: {reaction_file_path}")
