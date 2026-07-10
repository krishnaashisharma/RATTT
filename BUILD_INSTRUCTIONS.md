# Build Instructions for All Platforms

This document provides step-by-step instructions to build the Remote Device Management system for macOS, Windows, and Android.

## Prerequisites

### All Platforms
- Git
- Rust 1.70+ (for agent)
- Cargo

### macOS
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (optional): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Windows
- Visual Studio Build Tools or Visual Studio Community
- PowerShell 5.0 or higher
- Administrator privileges

### Android
- Android Studio
- Android SDK API 34
- Java Development Kit (JDK) 11 or higher
- Android NDK (for native compilation)

---

## Building for macOS

### Step 1: Prepare the Build Environment
```bash
cd /path/to/remote-device-mgmt
chmod +x deploy/macos-installer.sh
```

### Step 2: Run the Installer Script
```bash
bash deploy/macos-installer.sh
```

The script will:
- Build the Rust agent in release mode
- Create an app bundle
- Request Keychain permissions
- Create a LaunchDaemon for background execution
- Generate a DMG installer
- Place the DMG on your Desktop

### Step 3: Distribute the DMG
The generated DMG file (`RemoteDeviceAgent-0.1.0.dmg`) can be distributed to other macOS users. They can:
1. Double-click the DMG to mount it
2. Drag the app to Applications folder
3. Run the app (will prompt for permissions)

### Permissions Requested (macOS)
- ✓ Keychain access (for secure token storage)
- ✓ System tray access
- ✓ System monitoring (CPU, memory, processes)
- ✓ File system access
- ✓ Network access

---

## Building for Windows

### Step 1: Open PowerShell as Administrator
```powershell
# Right-click PowerShell and select "Run as administrator"
```

### Step 2: Navigate to the Project
```powershell
cd C:\path\to\remote-device-mgmt
```

### Step 3: Run the Installer Script
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy\windows-installer.ps1
```

The script will:
- Build the Rust agent in release mode
- Create installation directory at `C:\Program Files\RemoteDeviceAgent`
- Install the Windows Service
- Create firewall rules
- Create an uninstaller script
- Start the service automatically

### Step 4: Verify Installation
```powershell
Get-Service -Name "RemoteDeviceAgent"
```

### Permissions Requested (Windows)
- ✓ Administrator privileges (for service installation)
- ✓ DPAPI (for secure token storage)
- ✓ System monitoring (CPU, memory, processes)
- ✓ File system access
- ✓ Network access (port 8443)

### Uninstallation
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File "C:\Program Files\RemoteDeviceAgent\Uninstall.ps1"
```

---

## Building for Android

### Step 1: Set Up Android Studio
1. Download and install Android Studio
2. Open Android Studio and create a new project
3. Select "Empty Activity" template
4. Set minimum SDK to API 26 (Android 8.0)

### Step 2: Copy Project Files
```bash
# Copy the Android app files to your Android Studio project
cp deploy/android/AndroidManifest.xml app/src/main/
cp deploy/android/build.gradle app/
cp deploy/android/MainActivity.kt app/src/main/java/com/rdm/mobile/
```

### Step 3: Configure build.gradle (Project Level)
```gradle
plugins {
    id 'com.android.application' version '8.1.0' apply false
    id 'com.android.library' version '8.1.0' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.0' apply false
}
```

### Step 4: Build the APK
```bash
# In Android Studio terminal or command line
cd /path/to/android/project
./gradlew assembleRelease
```

The APK will be generated at:
```
app/build/outputs/apk/release/app-release.apk
```

### Step 5: Sign the APK (Production)
```bash
# Generate a keystore (first time only)
keytool -genkey -v -keystore remote-device-mgmt.keystore \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias remote-device-agent

# Sign the APK
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore remote-device-mgmt.keystore \
    app/build/outputs/apk/release/app-release.apk remote-device-agent

# Verify the signature
jarsigner -verify -verbose -certs \
    app/build/outputs/apk/release/app-release.apk
```

### Step 6: Optimize the APK
```bash
# Use zipalign to optimize the APK
zipalign -v 4 app/build/outputs/apk/release/app-release.apk \
    RemoteDeviceAgent-0.1.0.apk
```

### Permissions Requested (Android)
- ✓ INTERNET (for device communication)
- ✓ CAMERA (for QR code scanning of device tokens)
- ✓ LOCATION (optional, for device location tracking)
- ✓ STORAGE (for logs and data storage)
- ✓ BIOMETRIC (optional, for app-level security)

### Installation on Device
```bash
# Install via ADB
adb install RemoteDeviceAgent-0.1.0.apk

# Or distribute via Google Play Store, F-Droid, or direct download
```

---

## Distribution

### macOS Distribution
1. Generate the DMG: `bash deploy/macos-installer.sh`
2. Upload to your distribution server
3. Users download and double-click the DMG
4. Drag app to Applications folder
5. Launch and grant permissions

### Windows Distribution
1. Create an MSI installer (optional, using WiX Toolset)
2. Or distribute the PowerShell installer script
3. Users run as Administrator and execute the script
4. Service starts automatically

### Android Distribution
1. **Google Play Store**: Upload signed APK to Google Play Console
2. **F-Droid**: Submit to F-Droid repository
3. **Direct Download**: Host APK on your server
4. **Enterprise**: Use Mobile Device Management (MDM) solution

---

## Troubleshooting

### macOS
- **Permission Denied**: Run with `sudo`
- **Service Not Starting**: Check `/var/log/rdm-agent.log`
- **Keychain Issues**: Run `security set-key-partition-list -S apple-tool:,apple: -s -k <password> ~/Library/Keychains/login.keychain-db`

### Windows
- **Service Not Starting**: Check Event Viewer > Windows Logs > System
- **Firewall Issues**: Manually add rule in Windows Defender Firewall
- **Admin Privileges**: Right-click PowerShell and select "Run as administrator"

### Android
- **Build Fails**: Update Android SDK and Gradle
- **Permissions Not Granted**: Check Settings > Apps > Permissions
- **Connection Issues**: Verify network connectivity and firewall rules

---

## Security Notes

1. **Code Signing**: Always sign binaries before distribution
2. **HTTPS**: Ensure backend uses valid SSL certificates
3. **Permissions**: Only request necessary permissions
4. **Updates**: Verify update signatures before applying
5. **Audit Logs**: Monitor audit logs for suspicious activity

---

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review the threat model in `docs/threat-model.md`
3. Consult the API reference in `docs/api-reference.md`
