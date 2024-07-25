#!/usr/bin/env bash
ssh-agent bash -c 'ssh-add ~/.ssh/your-git-key; git push'