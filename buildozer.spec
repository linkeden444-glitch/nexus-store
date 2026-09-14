[app]
title = NEXUS UC Store
package.name = nexusapp
package.domain = com.pubg.kmo
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests, bin, venv, .buildozer, .git, .github, website, Apk, app
source.exclude_exts = spec, pyc, zip, md, yml, yaml, txt, cfg
version = 3.0.0
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna,openssl
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.build_tools_version = 33.0.2
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
# AUTO ACCEPT SDK LICENSES
android.accept_sdk_license = True
# PURE 64-BIT ARM ARCHITECTURE - High-performance modern 64-bit Android devices
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
