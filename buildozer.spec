[app]

# (str) Title of your application
title = SimplePush

# (str) Package name
package.name = simplepush

# (str) Package domain (reverse DNS style)
package.domain = org.example

# (str) Source code main file
source.main = main.py

# (str) Source directory
source.dir = .

# (list) Source files to include (extensions)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (used in build)
version = 0.1

# (list) Application requirements
requirements = python3,kivy==2.3.2,requests,plyer

# (str) Supported orientation (portrait or landscape)
orientation = portrait

# (list) Permissions for Android
android.permissions = INTERNET,VIBRATE,WAKE_LOCK

# (bool) Fullscreen mode
fullscreen = 0

# (str) Icon of the application (path relative to main.py)
# icon.filename = %(source.dir)s/icon.png

# (str) Presplash of the application (path relative to main.py)
# presplash.filename = %(source.dir)s/presplash.png

# (str) Supported Android API target
android.api = 33

# (str) Minimum Android API your APK will support
android.minapi = 21

# (str) Android SDK version
android.sdk = 33

# (str) Android NDK version
android.ndk = 25b

# (int) Android NDK API (minimum)
android.ndk_api = 21

# (bool) Copy library instead of linking
android.copy_libs = 1

# (list) Permissions for iOS (if needed)
# ios.permissions = CAMERA,LOCATION

# (str) Presplash background color
# presplash.color = #FFFFFF

# (str) Application icon background color (for Android adaptive icon)
# android.icon_background_color = #FFFFFF
