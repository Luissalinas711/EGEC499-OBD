# COLAB STARTUP CELL
# Paste as the first cell of the notebook and run it before anything else.
# Mounts Drive, sets up git, clones the repo, fetches the dataset, reports where it points.

from google.colab import drive, userdata
import os, subprocess, sys

# YOUR DETAILS
USER  = 'your-github-username'   # exactly as it appears in your repo URL
REPO  = 'EGEC499-OBD'            # the repository name
EMAIL = f'{USER}@users.noreply.github.com'   # GitHub > Settings > Emails shows yours.
SECRET = 'GITHUB_PAT'            # Colab secret holding a token with write access.
                                 # Key icon in the left sidebar, then enable for this notebook.

# THIS PROJECT'S DATASET 
CSV_NAME = 'EngineFaultDB_Final.csv'
CSV_URL  = 'https://raw.githubusercontent.com/leoxthomas/EngineFaultDB/main/EngineFaultDB_Final.csv'

REPO_PATH = f'/content/{REPO}'           # just a working folder, emptied on every restart
REPO_URL  = f'https://github.com/{USER}/{REPO}.git'
DRIVE     = f'/content/drive/MyDrive/{REPO}'      # results live here, so they survive a restart
CSV       = f'{REPO_PATH}/data/raw/{CSV_NAME}'

drive.mount('/content/drive')
assert os.path.isdir('/content/drive/MyDrive'), 'Drive did not mount, so results would go to a local folder instead'
os.system(f'git config --global user.name "{USER}"')
os.system(f'git config --global user.email "{EMAIL}"')

# Token in git's credential store, not in the remote URL
# /root is wiped on restart, so this is written every session.
PAT = userdata.get(SECRET)
if PAT:
    with open(os.path.expanduser('~/.git-credentials'), 'w') as handle:
        handle.write(f'https://{USER}:{PAT}@github.com\n')
    os.system('git config --global credential.helper store')
else:
    print(f'no {SECRET} secret: a public repo will clone, but nothing can be pushed')

# Clone only when the folder is missing. 
if not os.path.exists(REPO_PATH):
    os.system(f'git clone -q {REPO_URL} {REPO_PATH}')
assert os.path.exists(REPO_PATH), 'clone failed: check USER and REPO, and the token if the repo is private'

os.chdir(REPO_PATH)
sys.path.insert(0, REPO_PATH)
os.makedirs(f'{REPO_PATH}/data/raw', exist_ok=True)
os.makedirs(f'{DRIVE}/results', exist_ok=True)
os.makedirs(f'{DRIVE}/figures', exist_ok=True)

if not os.path.exists(CSV):
    os.system(f'curl -sL -o {CSV} {CSV_URL}')

# Where this session points
data = f'{os.path.getsize(CSV) / 1e6:.1f} MB' if os.path.exists(CSV) else 'MISSING'
results = os.listdir(f'{DRIVE}/results')
log = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True).stdout

print(f'repo     {os.getcwd()}')
print(f'drive    {DRIVE}')
print(f'data     {data}')
print(f'results  {len(results)} files')
print(f'\n{log.strip()}')
