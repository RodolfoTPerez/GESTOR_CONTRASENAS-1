"""
Cryptographic Configuration for PassGuardian

Centralized configuration for password hashing algorithms.
Supports both PBKDF2 (legacy) and Argon2id (modern).
"""

# ===== ARGON2 CONFIGURATION =====

# Enable Argon2 for new users (can be disabled for rollback)
ARGON2_ENABLED = True

# Auto-migrate existing users from PBKDF2 to Argon2 on login
AUTO_MIGRATE_ON_LOGIN = True

# Use Argon2 for new user registrations
USE_ARGON2_FOR_NEW_USERS = True

# Argon2 Parameters (Conservative settings for production)
# These values balance security and performance
ARGON2_TIME_COST = 3        # Number of iterations (default: 3)
ARGON2_MEMORY_COST = 65536  # Memory in KiB = 64 MB (default: 65536 = 64 MB)
ARGON2_PARALLELISM = 4      # Number of parallel threads (default: 4)
ARGON2_HASH_LEN = 32        # Output hash length in bytes
ARGON2_SALT_LEN = 16        # Salt length in bytes

# Expected performance: ~150ms login time on modern hardware
# Memory usage: ~32 MB per hash operation

# ===== PBKDF2 CONFIGURATION (Legacy) =====

# Current PBKDF2 settings (for backward compatibility)
PBKDF2_ITERATIONS = 100000  # Current iteration count
PBKDF2_HASH_ALGORITHM = 'sha256'
PBKDF2_KEY_LENGTH = 32      # Output key length in bytes

# OWASP 2024 recommendation for PBKDF2-SHA256
PBKDF2_ITERATIONS_OWASP_2024 = 600000

# Note: We keep PBKDF2_ITERATIONS at 100k for existing users
# New users will use Argon2 instead of upgrading PBKDF2

# ===== MIGRATION SETTINGS =====

# Log migration events for monitoring
LOG_MIGRATIONS = True

# Maximum time to wait for migration (seconds)
MIGRATION_TIMEOUT = 5

# Batch size for bulk migrations (if implemented)
MIGRATION_BATCH_SIZE = 100

# ===== ALGORITHM DETECTION =====

# Argon2 hashes start with this prefix
ARGON2_PREFIX = "$argon2"

# PBKDF2 hashes are hex strings (no prefix)
# Detection: if hash.startswith(ARGON2_PREFIX) → Argon2, else → PBKDF2
