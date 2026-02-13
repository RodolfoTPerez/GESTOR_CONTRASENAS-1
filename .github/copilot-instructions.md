# PassGuardian AI Coding Guidelines

## Architecture Overview

**PassGuardian** is a security-hardened password manager using clean architecture (Domain → Application → Infrastructure → Presentation). The app encrypts credentials locally with SQLite and syncs encrypted data to Supabase.

### Layer Responsibilities

- **Domain**: Business logic (no dependencies on crypto/DB)
- **Application**: Use cases and ports/interfaces
- **Infrastructure**: 
  - `crypto/` – Encryption primitives (Argon2id key derivation, AES-256-GCM, TOTP)
  - `db.py` / `storage/sqlcipher_adapter.py` – Encrypted local storage
  - `secrets_manager.py` – Secret CRUD + encryption/decryption
  - `user_manager.py` – User auth, TOTP, 2FA
  - `sync_manager.py` – Local↔Supabase sync with E2EE
- **Presentation**: PyQt5 UI (MVVM pattern), views separate from logic

### Key Data Flow

```
LoginView → UserManager (auth/2FA) → SecretsManager (unlock DB + derive key)
              ↓
DashboardView → SecretsManager (CRUD) ⟷ SyncManager (Supabase)
```

## Security-Critical Patterns

### Master Password & Key Derivation
- **Argon2id** (15 iterations, 128 MB, full CPU cores) for master password → 256-bit key
- **PBKDF2** (100k iterations) for user login hashing
- Salt stored in local DB; never exposed to Supabase
- `SecretsManager._derive_key()` and `UserManager.hash_password()` are the canonical implementations

### Encryption Standards
- **AES-256-GCM** for secret ciphertext (authenticated encryption)
- **HMAC-SHA512** for SQLCipher database integrity
- Nonce (12 bytes random) + ciphertext stored together; **never reuse nonce with same key**
- All secrets travel encrypted to Supabase; server cannot decrypt

### Critical: Memory Safety
- Derive temporary keys only when needed via `temporary_master_key()` context manager
- Always zero sensitive bytes after use (especially crypto keys and plaintext passwords)
- Example: `src/infrastructure/crypto/memory_wipe.py` with `secure_zero()`

### TOTP & 2FA
- `UserManager.generate_totp_secret()` creates a new 2FA secret (Base32-encoded)
- 2FA required for: export, master password change, sensitive account operations
- Verify TOTP token with `pyotp.TOTP.verify()` before allowing privileged actions

## Database & Sync

### Local Database (`passguardian.db`)
- SQLite with SQLCipher encryption (PRAGMA key, kdf_iter=256000)
- Tables: `meta` (salt), `users`, `secrets`, `audit_log`
- Secrets stored with: id, service, username, ciphertext, nonce, salt, owner, timestamps
- Each user has isolated secret storage via `owner` column

### Supabase Sync
- `SyncManager` handles bidirectional sync with conflict resolution
- **Secrets never stored plaintext in cloud**; format is `base64_nonce:base64_ciphertext`
- Sync only if internet detected (`_has_internet()` checks DNS)
- Automatic backup on every secret change if online

## Common Development Tasks

### Adding a Secret Field
1. Extend `secrets` table schema in `SecretsManager._create_secrets_table()`
2. Update `SecretsManager` methods: `add_secret()`, `get_secret()`, `update_secret()`
3. Add field to presentation layer (dashboard or dialog)
4. Update `SyncManager` to handle new field in cloud payload

### Adding a New User Action
1. Create use case in `src/application/use_cases/`
2. Implement in `SecretsManager` or `UserManager` (infrastructure layer)
3. Wire UI event to use case in presentation layer
4. Test with local DB **and** Supabase sync (if applicable)

### Testing Locally
- **No pytest coverage yet**; manual testing required
- To test encryption: `python -c "from src.infrastructure.security.crypto import encrypt_secret, decrypt_secret; ..."`
- To test DB: Initialize with `SecretsManager(None)` then `set_active_user(username, password)`

## Project-Specific Conventions

### Imports & Paths
- Always use `from pathlib import Path` for file I/O (cross-platform)
- Prefix sys.path with workspace root: `sys.path.insert(0, os.path.abspath(...))`
- Load env vars via `config/config.py` (reads `.env`, validates SUPABASE_URL/KEY)

### Error Handling
- Catch `cryptography.exceptions.InvalidTag` for authentication failures
- Supabase errors wrapped in `SyncManager` methods; propagate to UI with `QMessageBox`
- Never expose raw crypto errors to user; use friendly messages

### UI Patterns (PyQt5 + MVVM)
- **Views** (`src/presentation/`) only render state; no business logic
- **Callbacks** (e.g., `on_login_success`) decouple views from logic
- Master password dialog uses modal (`QDialog.exec()`)
- Always clear sensitive text fields after successful operations

## Integration Points

### Supabase
- Table: `secrets` with columns: `id`, `username`, `service`, `ciphertext`, `nonce`, `salt`, `owner`, `created_at`, `updated_at`
- API: POST/GET/PATCH via REST + API key from config
- **Row-level security** must verify owner matches authenticated user (not yet implemented)

### PyQt5
- Entry point: `src/main.py` → `start_app()`
- Config required: `QT_LOGGING_RULES` env var to silence Qt warnings
- Modals (2FA, change password) inherit from `QDialog`

## Avoid & Anti-Patterns

❌ **Don't hardcode secrets** – use `config/config.py`  
❌ **Don't skip key derivation** – always use Argon2id for master password  
❌ **Don't call DB methods from UI directly** – route through managers  
❌ **Don't reuse nonce+key pairs** – generate new nonce per secret  
❌ **Don't forget to wipe sensitive memory** – use `secure_zero()` or context managers  

## Quick Reference

| Task | File | Key Function |
|------|------|---------------|
| Encrypt/Decrypt | `src/infrastructure/security/crypto.py` | `encrypt_secret()`, `decrypt_secret()` |
| Manage Secrets CRUD | `src/infrastructure/secrets_manager.py` | `add_secret()`, `get_secret()`, `delete_secret()` |
| Handle Auth & 2FA | `src/infrastructure/user_manager.py` | `hash_password()`, `generate_totp_secret()` |
| Sync with Supabase | `src/infrastructure/sync_manager.py` | `push_secrets()`, `pull_secrets()` |
| UI Main Flow | `src/main.py`, `src/presentation/login_view.py` | `start_app()`, `on_login_success()` callback |

