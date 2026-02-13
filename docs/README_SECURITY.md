# PassGuardian – Security Hardened

## Quick start
1. pip install -r requirements-secure.txt
2. python -m src.bootstrap
3. pytest tests/

## What changed
- Argon2id 15 iter, 128 MB, full CPU cores
- SQLCipher local DB (AES-256-CTR + HMAC-SHA512)
- Memory wipe with ctypes
- Clean architecture (domain/application/infrastructure)
- No hard-coded secrets