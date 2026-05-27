#!/usr/bin/env node
'use strict';

/**
 * Stop hook — pushes the current branch to origin.
 * MUST run AFTER all autocommit-* hooks so their commits are included.
 * Best-effort: never breaks the Claude session on push failures.
 */

const path = require('node:path');
const { execFileSync } = require('node:child_process');

const PROJECT_ROOT = process.env.CLAUDE_PROJECT_DIR || path.resolve(__dirname, '..', '..');
try { process.chdir(PROJECT_ROOT); } catch { process.exit(0); }

const SILENT = { stdio: 'ignore' };

function git(args, opts = SILENT) {
  return execFileSync('git', args, opts);
}

try {
  try { git(['rev-parse', '--git-dir']); } catch { process.exit(0); }

  let remoteUrl;
  try {
    remoteUrl = execFileSync('git', ['remote', 'get-url', 'origin'], { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch { process.exit(0); }
  if (!remoteUrl) process.exit(0);

  let branch;
  try {
    branch = execFileSync('git', ['symbolic-ref', '--short', 'HEAD'], { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch { process.exit(0); }
  if (!branch) process.exit(0);

  let ahead = '0';
  try {
    const out = execFileSync('git', ['rev-list', '--count', `origin/${branch}..HEAD`], { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    ahead = out || '0';
  } catch {
    ahead = '1';
  }

  if (parseInt(ahead, 10) === 0) process.exit(0);

  try {
    git(['push', 'origin', `HEAD:${branch}`]);
  } catch {
    process.exit(0);
  }
} catch (_err) {
  process.exit(0);
}
