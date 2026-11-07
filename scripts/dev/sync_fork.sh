#!/bin/bash
set -xe
git fetch upstream
git checkout main
git lfs fetch upstream main
git lfs push origin main
git merge upstream/main
git push origin main
