[app]
title = Nexus UC Store
package.name = nexusapp
package.domain = com.pubg.kmo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests, bin, venv, .buildozer, .git, .github, website, Apk, app
source.exclude_exts = spec, pyc, zip, md, yml, yaml, txt, cfg
version = 1.0.0
android.numeric_version = 300002
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,chardet,idna,openssl
p4a.branch = v2024.01.21
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
# PREVENT UNNECESSARY SDK AUTO-UPDATE TO BROKEN BUILD-TOOLS 37
android.skip_update = True
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
# AUTO ACCEPT SDK LICENSES
android.accept_sdk_license = True
# UNIVERSAL ARCHITECTURE - Both 32-bit (armeabi-v7a) and 64-bit (arm64-v8a) devices
android.archs = arm64-v8a, armeabi-v7a
android.entrypoint = org.kivy.android.PythonActivity
android.release_artifact = apk
[buildozer]
log_level = 2
warn_on_root = 1
