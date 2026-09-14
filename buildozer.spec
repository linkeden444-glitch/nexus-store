[app]
title           = NEXUS UC Store
package.name    = nexusapp
package.domain  = com.pubg.kmo
source.dir          = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0.0
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,chardet,idna,openssl
orientation = portrait
fullscreen  = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api     = 33
android.minapi  = 24
android.ndk     = 25b
android.ndk_api = 24
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
# AUTO ACCEPT SDK LICENSES
android.accept_sdk_license = True
# PREVENT UNNECESSARY SDK AUTO-UPDATE TO BROKEN BUILD-TOOLS 37
android.skip_update = True
# PURE 64-BIT ARM ARCHITECTURE - Eliminates the 'This is 32-bit app' warning on all modern devices!
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.release_artifact = apk

[buildozer]
log_level    = 2
warn_on_root = 1
