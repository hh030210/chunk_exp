import json, os, sys
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import HfApi, snapshot_download
repo = sys.argv[1]
root = '/home/humq/chunk-baseline-experiments'
info = HfApi().model_info(repo)
print(json.dumps({'repo': repo, 'revision': info.sha}), flush=True)
path = snapshot_download(repo_id=repo, revision=info.sha, cache_dir=root+'/models/hub', max_workers=4)
print(json.dumps({'repo': repo, 'revision': info.sha, 'path': path}), flush=True)
