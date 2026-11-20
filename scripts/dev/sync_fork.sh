#!/bin/bash
set -xe

git fetch upstream
git checkout main
GIT_LFS_SKIP_SMUDGE=1 git merge upstream/main
git lfs fetch upstream upstream/main
git lfs checkout
git lfs push origin main
git push origin main
