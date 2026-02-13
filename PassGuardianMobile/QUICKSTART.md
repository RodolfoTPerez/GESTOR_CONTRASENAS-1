# PassGuardian Mobile - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd PassGuardianMobile
npm install
```

### Step 2: Start Development Server
```bash
npx expo start
```

### Step 3: Run on Device

**Option A: Physical Device (Recommended)**
1. Install **Expo Go** from App Store (iOS) or Play Store (Android)
2. Scan the QR code shown in terminal
3. App will load on your device

**Option B: Simulator/Emulator**
- Press `i` to open iOS Simulator (macOS only)
- Press `a` to open Android Emulator

## 📱 First Login

1. **Create Account**:
   - Email: `your-email@example.com`
   - Password: Strong master password (12+ chars)
   - Username: Your display name

2. **Test with Desktop Data**:
   - Use same email/password from desktop app
   - Your existing secrets will sync automatically!

## ✅ Verify It's Working

1. **Login**: Should see Vault screen after successful auth
2. **Sync**: Pull down to refresh - should load secrets from Supabase
3. **Decrypt**: Tap "COPY" on any credential - should copy to clipboard
4. **Search**: Type in search bar - should filter results

## 🔧 Troubleshooting

### "Cannot connect to Supabase"
- Check internet connection
- Verify Supabase URL in `src/config/config.js`
- Check Supabase project is running

### "Failed to decrypt"
- Master password must match desktop version
- User salt must be consistent (stored in Supabase users table)

### "Build failed"
```bash
# Clear cache and reinstall
rm -rf node_modules
npm install
npx expo start --clear
```

## 📦 Building for Production

### iOS (requires Apple Developer account)
```bash
# Configure app.json with your bundle ID
npx eas build --platform ios

# Or build locally
npx expo build:ios
```

### Android
```bash
# Build APK (for testing)
npx eas build --platform android --profile preview

# Build AAB (for Play Store)
npx eas build --platform android --profile production
```

## 🎯 Next Steps

1. **Add Biometrics**: Enable Face ID/Touch ID in settings
2. **Test Offline**: Turn off WiFi, verify offline access
3. **Customize Theme**: Edit colors in screen stylesheets
4. **Add Features**: Extend with password generator, health check, etc.

## 📚 Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Docs](https://reactnative.dev/docs/getting-started)
- [Supabase Docs](https://supabase.com/docs)

---

**Need Help?** Check ARCHITECTURE.md for technical details
