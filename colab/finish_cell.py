# COLAB FINISH CELL
# Paste as the last cell of the notebook and run it at the end of a session.
# Copies Drive results into the repo, then commits and pushes whatever changed.
# REPO_PATH and DRIVE come from the startup cell; a NameError here means it has not run.

import os, shutil, subprocess
from datetime import date

MSG = "EDIT THIS"   # what this session changed, in a few words. Becomes the commit message.

assert MSG != "EDIT THIS", "set MSG to what this session changed"
assert os.path.exists(os.path.expanduser('~/.git-credentials')), "run the startup cell first"

def git(*args):
    # Returns (ok, output) so a failure can be printed 
    done = subprocess.run(['git', '-C', REPO_PATH, *args], capture_output=True, text=True)
    return done.returncode == 0, (done.stdout + done.stderr).strip()


# Drive holds the results; the repo carries a copy so the record stays complete
for folder in ('results', 'figures'):
    shutil.copytree(f'{DRIVE}/{folder}', f'{REPO_PATH}/{folder}', dirs_exist_ok=True)

git('add', '-A')
staged = git('diff', '--cached', '--name-only')[1]
if not staged:
    print('nothing changed, so nothing to push')
else:
    print('staged:\n' + staged)
    git('commit', '-m', f'{date.today()} — {MSG}')
    ok, out = git('pull', '--rebase')
    if ok:
        ok, out = git('push')
    print('Pushed to GitHub.' if ok else out)
