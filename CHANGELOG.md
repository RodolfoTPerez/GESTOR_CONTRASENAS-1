# Changelog - PassGuardian v2 Sync & User Management Fixes

## 2026-02-16 - Critical Sync and User Management Improvements

### 🔧 Fixed: Duplicate Record Creation in Supabase
**Problem:** When updating existing records, the system was creating duplicates instead of updating them.

**Root Cause:**
1. Key mapping bug in `_row_to_dict` - `cloud_id` was mapped to `"id"` instead of `"cloud_id"`
2. Incorrect HTTP method - using POST (INSERT) for all operations instead of PATCH (UPDATE)

**Fix Applied:**
- Corrected `_row_to_dict` mapping in `sync_manager.py`
- Modified `_upload_record` to use PATCH for existing records, POST for new ones
- Added comprehensive error logging

**Files Modified:**
- `src/infrastructure/sync_manager.py` (lines 285-394)

---

### 🔧 Fixed: Missing integrity_hash Values
**Problem:** Legacy records and downloaded records had empty `integrity_hash` values, breaking data integrity checks.

**Root Cause:**
- Download logic (`_pull_cloud_to_local`, `restore_from_supabase`) didn't calculate hash when missing from cloud data

**Fix Applied:**
- Both methods now calculate `integrity_hash` from encrypted blob if missing: `hashlib.sha256(cipher).hexdigest()`
- Ensures all records have valid integrity hashes

**Files Modified:**
- `src/infrastructure/sync_manager.py` (lines 220-237, 95-122)

---

### 🔧 Fixed: Session Logout When Creating Secondary Users
**Problem:** Admin was logged out when creating secondary users, losing active session.

**Root Cause:**
- `add_new_user` called `set_active_user(new_username)` for ALL users, switching session context

**Fix Applied:**
- Now only calls `set_active_user` for the FIRST admin during initial setup
- Secondary users are created without switching active session

**Files Modified:**
- `src/infrastructure/user_manager.py` (line 676)

---

### 🔧 Fixed: Vault Key Not Available for Secondary User Creation
**Problem:** Creating secondary users failed with "No vault key available in current session"

**Root Cause:**
1. `cleanup_vault_cache()` was clearing session keys even when user was logged in
2. `_generate_user_keys` was looking for `self.sm.vault_key` instead of `self.sm.session.vault_key`

**Fix Applied:**
- Modified `cleanup_vault_cache()` to only clear session when NO user is logged in
- Corrected vault_key access path to use `self.sm.session.vault_key`

**Files Modified:**
- `src/infrastructure/secrets_manager.py` (lines 531-545)
- `src/infrastructure/user_manager.py` (lines 766-772)

---

### ✨ New Feature: Offline User Creation
**Description:** Users can now be created when internet is unavailable. They sync automatically to Supabase when connection is restored.

**Implementation:**
1. **Database Schema:** Added `synced` column to `users` table
2. **User Creation:** Modified `add_new_user()` to detect network errors and create users locally with temporary IDs
3. **Deferred Sync:** Added `sync_pending_users()` method to upload offline users when online
4. **Auto-Sync Integration:** Integrated into startup sync cycle

**Conflict Resolution:** "First-to-sync wins" strategy

**Files Modified:**
- `src/infrastructure/database/db_manager.py` (line 82)
- `src/infrastructure/user_manager.py` (lines 644-738)
- `src/infrastructure/sync_manager.py` (lines 27-126)
- `src/presentation/dashboard/dashboard_sync_actions.py` (lines 47-60)

---

### 🔧 Fixed: Silent Sync Failures
**Problem:** System reported "Inserted new record in Supabase" even when Supabase rejected the record.

**Root Cause:**
- `_upload_record` didn't verify if `post_records` actually succeeded
- Supabase could reject records (RLS policies, validations) without code detecting it

**Fix Applied:**
- Added verification query after INSERT to confirm record exists in Supabase
- Only logs success if record is verified
- Provides clear error messages when insertion fails

**Files Modified:**
- `src/infrastructure/sync_manager.py` (lines 384-410)

---

### 🔧 Fixed: Foreign Key Violations in Audit Logs
**Problem:** Audit log sync failed with foreign key constraint violations for orphaned `user_id` references.

**Root Cause:**
- Audit records had old `user_id` values that no longer existed in Supabase users table

**Fix Applied:**
- `sync_audit_logs()` now validates `user_id` exists in Supabase before syncing
- Skips orphaned audit records to prevent infinite retry loops
- Handles foreign key errors gracefully

**Files Modified:**
- `src/infrastructure/sync_manager.py` (lines 444-500)

---

## Summary of Changes

| Issue | Status | Impact |
|-------|--------|--------|
| Duplicate records on update | ✅ Fixed | No more duplicates in Supabase |
| Missing `integrity_hash` | ✅ Fixed | Data integrity maintained |
| Session logout on user creation | ✅ Fixed | Admins stay logged in |
| Vault key not available | ✅ Fixed | Secondary users created successfully |
| Offline user creation | ✅ Implemented | Full offline capability |
| Silent sync failures | ✅ Fixed | Accurate sync status reporting |
| Foreign key violations | ✅ Fixed | Audit logs sync without errors |

All changes maintain backward compatibility and include comprehensive error handling and logging.
