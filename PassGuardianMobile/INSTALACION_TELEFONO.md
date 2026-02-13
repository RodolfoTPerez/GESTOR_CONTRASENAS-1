# 📱 Cómo Poner PassGuardian en Tu Teléfono

## ✅ **MÉTODO 1: EXPO GO (MÁS FÁCIL - 5 MINUTOS)**

### Paso 1: Instalar Expo Go en Tu Teléfono

**Android:**
1. Abre Google Play Store
2. Busca "Expo Go"
3. Instala la app "Expo Go" (desarrollador: Expo)
4. Ábrela (no necesitas crear cuenta)

**iPhone (iOS):**
1. Abre App Store
2. Busca "Expo Go"
3. Instala la app "Expo Go" (desarrollador: 650 Industries, Inc.)
4. Ábrela (no necesitas crear cuenta)

### Paso 2: Instalar Dependencias en Tu PC

Abre PowerShell o Terminal en tu PC:

```powershell
# Navega a la carpeta de la app móvil
cd C:\PassGuardian_v2\PassGuardianMobile

# Instala las dependencias (toma 2-3 minutos)
npm install
```

### Paso 3: Iniciar el Servidor de Desarrollo

```powershell
# Inicia Expo
npx expo start
```

**Verás algo como esto:**
```
› Metro waiting on exp://192.168.1.100:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

   ▄▄▄▄▄▄▄ ▄ ▄  ▄ ▄▄▄▄▄▄▄
   █ ▄▄▄ █ ▀▄█▀▀▄ █ ▄▄▄ █
   █ ███ █ █ ▀ ▄▀ █ ███ █
   █▄▄▄▄▄█ ▄▀▄ █ █▄▄▄▄▄█
   ▄▄▄ ▄ ▄ ███▄▄  ▄ ▄ ▄▄▄
   ▄▄█▀▀▄▄▀▀█▄▀ ▀▀▄▀▄█▀▄▄
   ...
```

### Paso 4: Conectar Tu Teléfono

**IMPORTANTE:** Tu teléfono y tu PC deben estar en la MISMA red WiFi.

**Android:**
1. Abre la app **Expo Go** en tu Android
2. Toca "Scan QR Code"
3. Apunta la cámara al QR que aparece en la terminal
4. ¡La app se cargará automáticamente!

**iPhone:**
1. Abre la app de **Cámara** (la cámara nativa del iPhone)
2. Apunta al QR que aparece en la terminal
3. Toca la notificación "Abrir en Expo Go"
4. ¡La app se cargará automáticamente!

### Paso 5: Usar la App

1. La app PassGuardian se abrirá en tu teléfono
2. Verás la pantalla de Login
3. Ingresa tu email y master password (mismo que usas en desktop)
4. ¡Listo! Verás tus credenciales sincronizadas

---

## 🔧 **SOLUCIÓN DE PROBLEMAS**

### ❌ "No aparece el QR Code"
```powershell
# Detén el servidor (Ctrl+C) y vuelve a iniciar
npx expo start --clear
```

### ❌ "Cannot connect to Metro"
**Solución:** Usa el modo Tunnel (más lento pero funciona siempre)
```powershell
npx expo start --tunnel
```
Espera 30 segundos a que se conecte, luego escanea el QR.

### ❌ "Teléfono y PC en diferentes redes WiFi"
- Conecta ambos a la MISMA red WiFi
- O usa el modo tunnel: `npx expo start --tunnel`

### ❌ "Error: Metro bundler failed"
```powershell
# Limpia caché
cd C:\PassGuardian_v2\PassGuardianMobile
rm -r node_modules
npm install
npx expo start --clear
```

---

## 🚀 **MÉTODO 2: BUILD APK/IPA (PARA INSTALAR OFFLINE)**

Este método es más avanzado pero te da un archivo instalable.

### Para Android (APK)

1. Instala Expo CLI globalmente:
```powershell
npm install -g eas-cli
```

2. Login a Expo:
```powershell
eas login
# Si no tienes cuenta, regístrate gratis en expo.dev
```

3. Build el APK:
```powershell
cd C:\PassGuardian_v2\PassGuardianMobile
eas build --platform android --profile preview
```

4. Espera 10-15 minutos
5. Te dará un link para descargar el APK
6. Descarga el APK en tu Android
7. Instala el APK (permite instalación de fuentes desconocidas)

### Para iPhone (más complejo, requiere cuenta Apple Developer - $99/año)

No recomendado para pruebas. Usa Expo Go.

---

## 📋 **CHECKLIST RÁPIDO**

- [ ] Instalé Expo Go en mi teléfono
- [ ] Mi teléfono y PC están en la misma WiFi
- [ ] Corrí `npm install` en PassGuardianMobile
- [ ] Corrí `npx expo start`
- [ ] Vi el QR code en la terminal
- [ ] Escaneé el QR con Expo Go (Android) o Cámara (iOS)
- [ ] La app se cargó en mi teléfono
- [ ] Puedo hacer login con mi cuenta

---

## 💡 **TIPS PRO**

1. **Recarga Rápida**: Sacude tu teléfono → "Reload"
2. **Ver Errores**: Sacude tu teléfono → "Show Dev Menu" → "Debug Remote JS"
3. **Modo Oscuro**: Ya está configurado por defecto
4. **Desarrollo en Vivo**: Los cambios se reflejan automáticamente

---

## 🆘 **¿NECESITAS AYUDA?**

Si algo no funciona:
1. Asegúrate de tener Node.js instalado: `node --version`
2. Verifica que estés en la carpeta correcta: `cd C:\PassGuardian_v2\PassGuardianMobile`
3. Reinicia el servidor: Ctrl+C, luego `npx expo start`
