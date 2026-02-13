# PassGuardian Mobile 🛡️

**Enterprise-grade password manager for iOS & Android with end-to-end encryption**

## 🚀 Features

- ✅ **End-to-End Encryption**: AES-256-GCM encryption (compatible with desktop version)
- ✅ **Zero-Knowledge Architecture**: Your master password never leaves your device
- ✅ **Supabase Backend**: Real-time cloud sync across all devices
- ✅ **Biometric Authentication**: Face ID / Touch ID support
- ✅ **Cross-Platform**: iOS & Android from single codebase
- ✅ **Dark Mode UI**: Professional cybersecurity aesthetic
- ✅ **Offline Support**: Works without internet, syncs when connected

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- Expo CLI: `npm install -g expo-cli`
- iOS: Xcode (for iOS development)
- Android: Android Studio (for Android development)

## 🛠️ Installation

1. **Install dependencies**
```bash
cd PassGuardianMobile
npm install
```

2. **Configure Supabase**
   - Open `src/config/config.js`
   - Replace `SUPABASE_URL` and `SUPABASE_ANON_KEY` with your credentials
   - These are already configured for your project:
     ```javascript
     SUPABASE_URL: 'https://iymgmlxlvjsqxiwdznac.supabase.co'
     SUPABASE_ANON_KEY: '...' // Already set
     ```

3. **Start development server**
```bash
npx expo start
```

4. **Run on device/simulator**
   - Press `i` for iOS Simulator
   - Press `a` for Android Emulator
   - Scan QR code with Expo Go app on your phone

## 📱 Building for Production

### iOS (requires macOS)
```bash
npx expo build:ios
```

### Android
```bash
npx expo build:android
```

## 🔐 Security Architecture

### Encryption Flow
1. User enters master password
2. PBKDF2 derives 256-bit encryption key (100,000 iterations)
3. Secrets encrypted with AES-256-GCM before sending to Supabase
4. Decryption happens client-side only
5. Master password NEVER transmitted or stored

### Compatibility
- **Desktop Version**: Uses same AES-GCM + PBKDF2 algorithm
- **Data Format**: Fully compatible - secrets can be created on mobile and accessed on desktop (and vice versa)

## 📂 Project Structure

```
PassGuardianMobile/
├── src/
│   ├── config/
│   │   └── config.js          # Supabase & crypto configuration
│   ├── services/
│   │   ├── authService.js     # Supabase authentication
│   │   ├── cryptoService.js   # AES-GCM encryption/decryption
│   │   └── vaultService.js    # CRUD operations for secrets
│   └── screens/
│       ├── LoginScreen.js     # Login/SignUp UI
│       └── VaultScreen.js     # Vault management UI
├── App.js                     # Main app entry point
├── package.json
└── README.md
```

## 🎨 UI/UX Features

- **Dark Mode Cybersecurity Theme**: Professional navy blue (#0f172a) with electric blue accents (#3b82f6)
- **Smooth Animations**: Native performance with React Native Reanimated
- **Gesture Support**: Swipe actions, pull-to-refresh
- **Haptic Feedback**: Touch feedback on supported devices

## 🔧 Available Scripts

- `npm start` - Start Expo development server
- `npm run android` - Run on Android
- `npm run ios` - Run on iOS
- `npm run web` - Run in web browser (limited functionality)

## 🚨 Important Notes

1. **Master Password**: Cannot be recovered if lost - store securely!
2. **Biometric Setup**: Enable in device settings before first use
3. **Internet Required**: For initial setup and sync (works offline after)
4. **Supabase RLS**: Row-level security ensures users only see their own data

## 📈 Roadmap

- [ ] Biometric quick unlock
- [ ] Password strength analyzer
- [ ] Breach detection integration
- [ ] Auto-fill support (iOS/Android)
- [ ] Secure notes support
- [ ] Team sharing features
- [ ] Dark web monitoring

## 🔗 Related Projects

- **PassGuardian Desktop** (Python/PyQt5): Windows/Mac/Linux client

## 📄 License

Private - Enterprise Use Only

## 🤝 Support

For issues or questions, contact the development team.

---

**Built with React Native + Expo + Supabase**
**Secured with AES-256-GCM + PBKDF2**
