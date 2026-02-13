# PassGuardian Mobile - Technical Architecture

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MOBILE APPLICATION                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │              React Native + Expo                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │    │
│  │  │   UI Layer   │  │   Services   │  │  Crypto  │ │    │
│  │  │  (Screens)   │→ │  (Business)  │→ │  (AES)   │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓ HTTPS                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Supabase Client SDK                    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE CLOUD                            │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐   │
│  │  Auth Service  │  │  PostgreSQL    │  │  Realtime   │   │
│  │   (JWT/2FA)    │  │  (with RLS)    │  │  (Sync)     │   │
│  └────────────────┘  └────────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Encryption Architecture

### Key Derivation (PBKDF2)
```javascript
Master Password + User Salt
         ↓ PBKDF2-SHA256 (100,000 iterations)
    256-bit AES Key
```

### Encryption Flow (AES-256-GCM)
```
Plaintext Password
    ↓
[AES-GCM Encrypt]
    ├─ Key: Derived from master password
    ├─ IV: Random 12 bytes
    └─ Tag: 16 bytes (authentication)
    ↓
Base64(IV + Ciphertext + Tag)
    ↓
Store in Supabase
```

### Decryption Flow
```
Encrypted Data from Supabase
    ↓
Base64 Decode
    ↓
Extract: IV (12) + Ciphertext + Tag (16)
    ↓
[AES-GCM Decrypt]
    └─ Key: Derived from master password
    ↓
Plaintext Password
```

## 📊 Database Schema (Supabase)

### `secrets` table
```sql
CREATE TABLE secrets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    vault_id UUID,
    service VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    secret TEXT NOT NULL,              -- Encrypted password
    is_private BOOLEAN DEFAULT false,
    notes TEXT,
    synced BOOLEAN DEFAULT false,
    deleted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE secrets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own secrets"
    ON secrets FOR ALL
    USING (auth.uid() = user_id);
```

## 🔄 Data Flow

### Creating a New Secret
```
1. USER: Enters service, username, password
2. APP: Derives encryption key from master password
3. APP: Encrypts password with AES-256-GCM
4. APP: Sends encrypted data to Supabase
5. SUPABASE: Validates user (JWT), applies RLS
6. SUPABASE: Stores encrypted secret
7. APP: Updates local state
```

### Reading Secrets
```
1. APP: Fetches encrypted secrets from Supabase
2. SUPABASE: Returns only user's secrets (RLS)
3. APP: Decrypts passwords client-side
4. USER: Views/copies decrypted passwords
```

## 🛡️ Security Layers

### Layer 1: Transport Security
- HTTPS/TLS for all network requests
- Certificate pinning (production)

### Layer 2: Authentication
- Supabase JWT tokens
- 2FA/TOTP support
- Biometric (Face ID/Touch ID)

### Layer 3: Authorization
- Row Level Security (RLS) in PostgreSQL
- Users can ONLY access their own data

### Layer 4: Encryption
- End-to-end encryption (E2EE)
- Zero-knowledge architecture
- Master password never transmitted

### Layer 5: Storage
- Secure key storage (Keychain/KeyStore)
- Encrypted local cache
- Auto-lock on app background

## 📱 Platform-Specific Features

### iOS
- Face ID / Touch ID
- Keychain for secure storage
- App Groups for extensions (future)
- Auto-fill credential provider (future)

### Android
- Fingerprint / Face Unlock
- KeyStore for secure storage
- Autofill Service (future)

## 🚀 Performance Optimizations

1. **Lazy Loading**: Secrets loaded on-demand
2. **Pagination**: 50 secrets per page
3. **Caching**: Encrypted cache with TTL
4. **Realtime Sync**: Only syncs changes, not full dataset
5. **Background Fetch**: Pre-fetches when app opens

## 🔄 Sync Strategy

### Conflict Resolution
```
1. Last-write-wins (based on updated_at timestamp)
2. Soft deletes prevent data loss
3. Manual merge for conflicts (future feature)
```

### Offline Support
```
1. SQLite local database mirrors Supabase
2. Queue operations when offline
3. Sync queue when connection restored
4. Show sync status to user
```

## 🧪 Testing Strategy

1. **Unit Tests**: Crypto functions, services
2. **Integration Tests**: Supabase API calls
3. **E2E Tests**: Full user flows with Detox
4. **Security Audit**: Penetration testing

## 📈 Scalability

- **Users**: Unlimited (Supabase scales)
- **Secrets per User**: 10,000+ recommended limit
- **Concurrent Syncs**: Handled by Supabase Realtime
- **API Rate Limits**: Supabase tier-dependent

## 🔮 Future Enhancements

1. **Hardware Security Module (HSM)** integration
2. **WebAuthn / Passkeys** support
3. **Secure enclave** for key storage (iOS)
4. **Encrypted file attachments**
5. **Emergency access** delegation
6. **Password health** monitoring
7. **Dark web monitoring** integration

## 🛠️ Development Tools

- **React Native Debugger**: UI inspection
- **Flipper**: Network, DB, Layout debugging
- **Sentry**: Error tracking (production)
- **Firebase Analytics**: Usage metrics

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-30  
**Maintained by**: PassGuardian Team
