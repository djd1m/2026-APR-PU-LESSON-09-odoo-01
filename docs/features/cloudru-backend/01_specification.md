# Feature Specification: Cloud.ru Foundation Models Backend

> **Feature ID:** cloudru-backend
> **Date:** 2026-05-27
> **Complexity:** Low (extends existing vLLM backend)

## Overview

Add Cloud.ru Evolution Foundation Models as a pre-configured provider for the vLLM CV backend. Cloud.ru uses an OpenAI-compatible API at `https://foundation-models.api.cloud.ru/v1/` — so our existing VLLMDetector works out of the box. This feature adds convenience: pre-configured presets, documentation, and a test script.

## Changes

1. **Preset configurations** in .env.example for Cloud.ru (API URL, model names)
2. **Test script** that runs the vLLM detector on downloaded test photos and prints results
3. **Documentation** update for Cloud.ru setup
4. **.env.example** with Cloud.ru-specific examples

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|:------------:|
| 1 | Cloud.ru API works with existing VLLMDetector (no code changes to detector) | Integration test |
| 2 | .env.example has Cloud.ru preset section | Code review |
| 3 | Test script runs on downloaded photos and prints stage/confidence/explanation | Manual test |
| 4 | Documentation explains Cloud.ru registration and API key setup | Code review |
