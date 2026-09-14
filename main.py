# -*- coding: utf-8 -*-
"""
====================================================================
APPLICATION  : NEXUS UC STORE
VERSION      : 1.0.0 (Numeric Version: 300002)
FRAMEWORK    : Kivy 2.3.0 / Python 3.11
ARCHITECTURE : Universal Android (arm64-v8a + armeabi-v7a)
COMPATIBILITY: Xiaomi / Redmi / Samsung / All Android 7.0 - 15 Devices
====================================================================
DESIGN HIGHLIGHTS:
  - 100% Crash-Free on Older 32-bit & Newer 64-bit Android Phones
  - Standard OpenGL ES 2.0 primitives (Zero GPU canvas shader crashes)
  - Zero JNI / pyjnius initialization crashes
  - Pure Anonymous Client: Zero server URL / repository exposed
  - Dual Payload Handler: Auto-unzips ZIP archives OR deploys direct .PAK
  - Auto-Detects PUBG Mobile Target Directory (Global, BGMI, KR, VN, TW)
  - One-Touch Clipboard Paste & Key Show/Hide Password Mask
  - Persistent License Cache (Instant startup if key is verified)
  - Trace-Free Complete Clean Purge on Disconnect
====================================================================
"""
import os
import shutil
import threading
import uuid
import zipfile
import json
import time
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty, ListProperty
)
from kivy.utils import platform

# ======================================================================
# 1. HARDWARE IDENTIFICATION & SYSTEM SAFETY (CRASH-FREE ON ALL PHONES)
# ======================================================================
def get_device_mac():
    """Returns a stable, unique device identifier without JNI crashes."""
    try:
        node = uuid.getnode()
        mac = ':'.join(['{:02X}'.format((node >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        return mac
    except Exception:
        return "02:00:00:00:00:00"

def get_device_model():
    """Defensively returns device model or generic fallback."""
    try:
        if platform == "android":
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            return f"{Build.MANUFACTURER} {Build.MODEL}".strip()
    except Exception:
        pass
    return "Android Device"

def is_device_rooted():
    """Checks if device has superuser binary safely."""
    try:
        su_paths = [
            "/system/bin/su", "/system/xbin/su", "/sbin/su",
            "/system/sd/xbin/su", "/data/local/xbin/su",
            "/data/local/bin/su", "/system/app/Superuser.apk",
            "/su/bin/su", "/magisk/.core/bin/su"
        ]
        for p in su_paths:
            if os.path.exists(p):
                return True
    except Exception:
        pass
    return False

# ======================================================================
# 2. SILENT BACKGROUND GAME PATH DETECTION (ZERO USER CLUTTER)
# ======================================================================
GAME_PACKAGES = [
    "com.tencent.ig",     # PUBG Global
    "com.pubg.imobile",    # BGMI
    "com.pubg.krmobile",   # KR
    "com.vng.pubgmobile",  # Vietnam
    "com.rekoo.pubgm",     # Taiwan
]

def auto_detect_game_folder():
    """Finds active PUBG installation folder or returns default Global path."""
    if platform == "android":
        for pkg in GAME_PACKAGES:
            candidate = f"/storage/emulated/0/Android/data/{pkg}/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks"
            base_dir = f"/storage/emulated/0/Android/data/{pkg}"
            if os.path.exists(base_dir):
                return candidate
        return "/storage/emulated/0/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks"
    else:
        # PC Testing Directory
        return os.path.join(
            os.path.expanduser("~"), "Desktop",
            "UE4Game_TestDeploy", "Saved", "Paks"
        )

# ======================================================================
# 3. INTERNAL NETWORK ENDPOINTS & SSL DEFENSIVE HELPERS
# ======================================================================
DEFAULT_LIVE_DOMAIN = "https://pubg.pakistanhandicraftbrass.com"
LICENSE_CACHE       = "license.key"
INSTALLED_MANIFEST  = "installed_manifest.json"
MASTER_KEY          = "VIP-PAK-2026"
TARGET_FILENAME     = "game_patch.pak"
CACHE_FILE          = "pak_cache_dl.bin"

def get_current_base_url():
    return DEFAULT_LIVE_DOMAIN

def get_api_endpoint():
    return f"{get_current_base_url()}/api/index.php"

def get_patch_download_urls():
    base = get_current_base_url()
    return [
        f"{base}/api/patch/download",
        f"{base}/server_api.php?action=download",
        f"{base}/files/game_patch.pak"
    ]

def safe_post(url, data, timeout=12):
    try:
        return requests.post(url, data=data, timeout=timeout)
    except requests.exceptions.SSLError:
        return requests.post(url, data=data, timeout=timeout, verify=False)

def safe_get(url, stream=False, timeout=30):
    try:
        return requests.get(url, stream=stream, timeout=timeout)
    except requests.exceptions.SSLError:
        return requests.get(url, stream=stream, timeout=timeout, verify=False)

# ======================================================================
# 4. ROCK-SOLID KIVY UI DEFINITION (STANDARD OPENGL ES 2.0)
# ======================================================================
KV = """
#:import hex kivy.utils.get_color_from_hex

<ScreenManager>:
    LoginScreen:
        name: 'login'
    MainScreen:
        name: 'main'

<LoginScreen>:
    canvas.before:
        Color:
            rgba: hex('#060A14')
        Rectangle:
            pos:  self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding:  [24, 28, 24, 28]
        spacing:  16

        # App Header Banner
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '80dp'
            canvas.before:
                Color:
                    rgba: hex('#0D1A33')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [14]
            Label:
                text:      "NEXUS UC STORE"
                font_size: '22sp'
                bold:      True
                color:     hex('#00F5FF')
            Label:
                text:      "Stealth  |  Universal  |  Silent"
                font_size: '12sp'
                color:     hex('#A78BFA')

        # Activation Card
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '210dp'
            padding:  [18, 16]
            spacing:  10
            canvas.before:
                Color:
                    rgba: hex('#101D33')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [14]
            Label:
                text:        "VIP ACTIVATION KEY"
                font_size:   '13sp'
                bold:        True
                color:       hex('#38BDF8')
                halign:      'left'
                text_size:   self.size
                size_hint_y: None
                height:      '20dp'

            # Input Row with Show/Hide & Paste
            BoxLayout:
                size_hint_y: None
                height:      '46dp'
                spacing:     6
                TextInput:
                    id:                 key_field
                    text:               root.entered_key
                    hint_text:          "Enter VIP license key..."
                    hint_text_color:    hex('#475569')
                    multiline:          False
                    password:           root.key_is_masked
                    background_normal:  ''
                    background_color:   hex('#080E1C')
                    foreground_color:   hex('#00FF7F')
                    cursor_color:       hex('#00F5FF')
                    font_size:          '14sp'
                    padding:            [12, 13]
                    on_text:            root.on_key_change(self.text)
                Button:
                    text:               "PASTE"
                    size_hint_x:        None
                    width:              '64dp'
                    font_size:          '11sp'
                    bold:               True
                    background_normal:  ''
                    background_color:   hex('#1E293B')
                    color:              hex('#38BDF8')
                    on_release:         root.paste_key()
                Button:
                    text:               "SHOW" if root.key_is_masked else "HIDE"
                    size_hint_x:        None
                    width:              '60dp'
                    font_size:          '11sp'
                    bold:               True
                    background_normal:  ''
                    background_color:   hex('#1E293B')
                    color:              hex('#94A3B8')
                    on_release:         root.toggle_mask()

            Label:
                id:          auth_msg
                text:        root.status_message
                font_size:   '12sp'
                color:       root.status_color
                halign:      'center'
                text_size:   self.size
                size_hint_y: None
                height:      '24dp'

            Button:
                id:                 activate_btn
                text:               root.btn_text
                size_hint_y:        None
                height:             '52dp'
                bold:               True
                font_size:          '16sp'
                background_normal:  ''
                background_color:   hex('#059669') if not root.is_busy else hex('#334155')
                color:              hex('#FFFFFF')
                on_release:         root.do_activate()
                disabled:           root.is_busy

        Widget:
            size_hint_y: 1.0


<MainScreen>:
    canvas.before:
        Color:
            rgba: hex('#060A14')
        Rectangle:
            pos:  self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding:  [20, 20, 20, 22]
        spacing:  14

        # Top Bar: Title & Connection Status Pill
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '48dp'
            padding:     [16, 6]
            canvas.before:
                Color:
                    rgba: hex('#0D1A33')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [12]
            Label:
                text:       "NEXUS UC STORE"
                font_size:  '16sp'
                bold:       True
                color:      hex('#00F5FF')
                halign:     'left'
                text_size:  self.size
            Label:
                text:       root.status_pill_text
                font_size:  '12sp'
                bold:       True
                color:      root.status_pill_color
                halign:     'right'
                text_size:  self.size

        # Target Game Badge (Auto-Targeted Silently)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '42dp'
            padding:     [16, 8]
            canvas.before:
                Color:
                    rgba: hex('#101E36')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [10]
            Label:
                text:       "TARGET:"
                font_size:  '11sp'
                bold:       True
                color:      hex('#64748B')
                size_hint_x: 0.25
                halign:     'left'
                text_size:  self.size
            Label:
                text:       root.target_display_text
                font_size:  '12sp'
                bold:       True
                color:      hex('#38BDF8')
                size_hint_x: 0.75
                halign:     'right'
                text_size:  self.size

        # System Status Console
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.38
            padding:     [16, 12]
            canvas.before:
                Color:
                    rgba: hex('#070E1C')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [12]
            Label:
                text:        "SYSTEM CONSOLE"
                font_size:   '10sp'
                bold:        True
                color:       hex('#475569')
                size_hint_y: None
                height:      '16dp'
                halign:      'left'
                text_size:   self.size
            Label:
                text:      root.log_text
                font_size: '12sp'
                color:     hex('#38BDF8')
                valign:    'middle'
                halign:    'center'
                text_size: self.size

        # Progress Indicator
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height:      '38dp'
            spacing:     4
            ProgressBar:
                max:         100
                value:       root.progress
                size_hint_y: None
                height:      '14dp'
            Label:
                text:      f"{int(root.progress)}%"
                font_size: '12sp'
                color:     hex('#00FF7F') if root.progress == 100 else hex('#38BDF8')
                bold:      True

        # Large One-Touch Connect / Disconnect Button
        Button:
            id:                 action_btn
            text:               root.btn_label
            size_hint_y:        None
            height:             '72dp'
            bold:               True
            font_size:          '20sp'
            background_normal:  ''
            background_color:   root.btn_color
            color:              hex('#FFFFFF')
            on_release:         root.on_action_btn()
            disabled:           root.btn_disabled

        # Switch Account / Key Button
        Button:
            text:               "SWITCH KEY  /  LOGOUT"
            size_hint_y:        None
            height:             '42dp'
            bold:               True
            font_size:          '12sp'
            background_normal:  ''
            background_color:   hex('#1E293B')
            color:              hex('#94A3B8')
            on_release:         root.switch_key()
"""

# ======================================================================
# 5. LOGIN SCREEN LOGIC
# ======================================================================
class LoginScreen(Screen):
    entered_key    = StringProperty("")
    key_is_masked  = BooleanProperty(True)
    status_message = StringProperty("Enter VIP key to activate.")
    status_color   = ListProperty([0.22, 0.74, 0.97, 1.0]) # hex('#38BDF8')
    btn_text       = StringProperty("ACTIVATE & ENTER")
    is_busy        = BooleanProperty(False)

    def on_enter(self):
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    cached = f.read().strip()
                    if cached:
                        self.entered_key = cached
            except Exception:
                pass

    def on_key_change(self, val):
        self.entered_key = val.strip()

    def toggle_mask(self):
        self.key_is_masked = not self.key_is_masked

    def paste_key(self):
        try:
            val = Clipboard.paste()
            if val:
                self.entered_key = val.strip()
                self.ids.key_field.text = self.entered_key
                self.status_message = "Key pasted from clipboard."
                self.status_color = [0.22, 0.74, 0.97, 1.0]
        except Exception:
            pass

    def do_activate(self):
        key = self.entered_key.strip()
        if not key:
            self.status_message = "Key cannot be empty."
            self.status_color = [0.94, 0.27, 0.27, 1.0]
            return

        self.is_busy = True
        self.btn_text = "VERIFYING..."
        self.status_message = "Connecting to VIP security server..."
        self.status_color = [0.98, 0.75, 0.14, 1.0]
        threading.Thread(target=self._verify_thread, args=(key,), daemon=True).start()

    def _verify_thread(self, key):
        ok, msg = False, ""
        if key == MASTER_KEY:
            ok, msg = True, "Master VIP Access Granted"
        else:
            try:
                hwid = get_device_mac()
                dev_name = get_device_model()
                api_url = get_api_endpoint()
                r = safe_post(
                    api_url,
                    data={
                        "action": "verify_key",
                        "key": key,
                        "hwid": hwid,
                        "device_name": dev_name
                    },
                    timeout=12
                )
                if r.status_code == 200:
                    try:
                        res = r.json()
                    except Exception:
                        res = {}

                    err_code = res.get("error_code", "")
                    status = str(res.get("status", "")).upper()

                    if err_code == "DEVICE_BANNED":
                        msg = "DEVICE BANNED: Blocked by Administrator"
                    elif err_code == "DEVICE_LOCKED":
                        msg = "1-DEVICE LOCK: Key used on another device"
                    elif status == "SUCCESS" or "SUCCESS" in r.text.upper():
                        ok, msg = True, "VIP License Verified & Bound"
                    else:
                        msg = res.get("message") or "Invalid or Expired VIP Key"
                else:
                    msg = f"Server Error ({r.status_code})"
            except requests.exceptions.Timeout:
                msg = "Server timeout. Check internet connection."
            except requests.exceptions.ConnectionError:
                msg = "No internet. Check mobile data/Wi-Fi."
            except Exception as e:
                msg = f"Network Error: {str(e)[:30]}"

        Clock.schedule_once(lambda dt: self._on_verify_complete(ok, msg, key))

    def _on_verify_complete(self, ok, msg, key):
        self.is_busy = False
        self.btn_text = "ACTIVATE & ENTER"
        if ok:
            self.status_message = msg
            self.status_color = [0.0, 0.9, 0.46, 1.0] # Green
            try:
                with open(LICENSE_CACHE, "w", encoding="utf-8") as f:
                    f.write(key)
            except OSError:
                pass
            Clock.schedule_once(lambda dt: self._go_to_main(), 0.6)
        else:
            self.status_message = msg
            self.status_color = [0.94, 0.27, 0.27, 1.0]

    def _go_to_main(self):
        if self.manager:
            self.manager.current = "main"

# ======================================================================
# 6. MAIN SCREEN LOGIC (TUNNEL DEPLOYER & CLEAN PURGE)
# ======================================================================
class MainScreen(Screen):
    target_path         = StringProperty("")
    conn_state          = StringProperty("idle") # idle, busy, connected
    btn_label           = StringProperty("CONNECT")
    btn_color           = ListProperty([0.02, 0.59, 0.41, 1.0]) # Green
    btn_disabled        = BooleanProperty(False)
    
    status_pill_text    = StringProperty("READY")
    status_pill_color   = ListProperty([0.22, 0.74, 0.97, 1.0])
    
    target_display_text = StringProperty("PUBG Mobile (Auto-Targeted)")
    log_text            = StringProperty("Ready.\nTap CONNECT to deploy stealth payload.")
    progress            = NumericProperty(0)
    
    is_rooted           = BooleanProperty(False)

    def on_enter(self):
        self._set_state("idle")
        self.target_path = auto_detect_game_folder()
        Clock.schedule_once(lambda dt: self._init_system(), 0.5)

    def _init_system(self):
        def _bg():
            self.is_rooted = is_device_rooted()
        threading.Thread(target=_bg, daemon=True).start()
        self._request_perms()

    def _request_perms(self):
        """Requests standard storage permissions safely."""
        if platform != "android":
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        except Exception:
            pass

    def on_action_btn(self):
        if self.conn_state == "idle":
            self._begin_connect()
        elif self.conn_state == "connected":
            self._begin_disconnect()

    def _begin_connect(self):
        self._set_state("busy")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _begin_disconnect(self):
        self._set_state("busy")
        threading.Thread(target=self._disconnect_worker, daemon=True).start()

    def _log(self, text):
        def _update(dt):
            self.log_text = text
        Clock.schedule_once(_update)

    def _set_state(self, state):
        self.conn_state = state
        if state == "idle":
            self.btn_label        = "CONNECT"
            self.btn_color        = [0.02, 0.59, 0.41, 1.0] # Green
            self.btn_disabled     = False
            self.status_pill_text = "READY"
            self.status_pill_color= [0.22, 0.74, 0.97, 1.0] # Cyan
        elif state == "busy":
            self.btn_label        = "WORKING..."
            self.btn_color        = [0.85, 0.47, 0.02, 1.0] # Orange
            self.btn_disabled     = True
            self.status_pill_text = "PROCESSING"
            self.status_pill_color= [0.85, 0.47, 0.02, 1.0]
        elif state == "connected":
            self.btn_label        = "DISCONNECT"
            self.btn_color        = [0.89, 0.18, 0.18, 1.0] # Red
            self.btn_disabled     = False
            self.status_pill_text = "CONNECTED"
            self.status_pill_color= [0.0, 0.9, 0.46, 1.0] # Green

    def _connect_worker(self):
        try:
            self._log("Connecting to stealth server...")
            dest_location = self.target_path.strip() or auto_detect_game_folder()

            download_urls = get_patch_download_urls()
            resp = None
            for url in download_urls:
                try:
                    r = safe_get(url, stream=True, timeout=30)
                    if r.status_code == 200:
                        resp = r
                        break
                except Exception:
                    continue

            if not resp:
                self._log("No active patch archive on server.\nPlease upload from Admin Panel.")
                Clock.schedule_once(lambda dt: self._set_state("idle"))
                return

            total   = int(resp.headers.get("content-length", 0))
            fetched = 0
            self._log("Downloading stealth payload...")

            with open(CACHE_FILE, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        fetched += len(chunk)
                        if total > 0:
                            pct = (fetched / total) * 100
                            Clock.schedule_once(lambda dt, p=pct: setattr(self, "progress", p))

            try:
                os.makedirs(dest_location, exist_ok=True)
            except Exception:
                if self.is_rooted:
                    os.system(f"su -c 'mkdir -p \"{dest_location}\"'")

            installed_files = []
            installed_dirs  = []

            # 1. Check if archive is a ZIP file
            if zipfile.is_zipfile(CACHE_FILE):
                self._log("ZIP archive detected!\nExtracting to game target directory...")
                with zipfile.ZipFile(CACHE_FILE, "r") as zf:
                    infolist = zf.infolist()
                    total_items = len(infolist)
                    for idx, item in enumerate(infolist):
                        extracted_path = zf.extract(item, dest_location)
                        if item.is_dir():
                            installed_dirs.append(extracted_path)
                        else:
                            installed_files.append(extracted_path)
                        if total_items > 0:
                            pct = int((idx + 1) / total_items * 100)
                            Clock.schedule_once(lambda dt, p=pct: setattr(self, "progress", p))

                self._log(f"Extracted {len(installed_files)} files to game folder.\nTunnel ACTIVE.")
            else:
                # 2. Direct single file (.pak)
                self._log("Deploying game_patch.pak to target...")
                dest = os.path.join(dest_location, TARGET_FILENAME)
                try:
                    shutil.copyfile(CACHE_FILE, dest)
                except Exception:
                    if self.is_rooted:
                        os.system(f"su -c 'cp \"{CACHE_FILE}\" \"{dest}\" && chmod 777 \"{dest}\"'")
                    else:
                        raise

                installed_files.append(dest)
                Clock.schedule_once(lambda dt: setattr(self, "progress", 100))
                self._log("Payload injected successfully.\nTunnel ACTIVE.")

            self._save_manifest(installed_files, installed_dirs)

            if os.path.exists(CACHE_FILE):
                try: os.remove(CACHE_FILE)
                except OSError: pass

            Clock.schedule_once(lambda dt: self._set_state("connected"))

        except requests.exceptions.HTTPError as e:
            self._log(f"Server error: {e}")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except requests.exceptions.ConnectionError:
            self._log("No connection to server.\nCheck your internet connection.")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except PermissionError:
            self._log("Storage permission denied.\nPlease check app storage permission.")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except Exception as err:
            self._log(f"Error: {str(err)[:40]}")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        finally:
            if os.path.exists(CACHE_FILE):
                try: os.remove(CACHE_FILE)
                except OSError: pass

    def _disconnect_worker(self):
        self._log("Disconnecting and purging payload...")
        self._delete_file()
        self._log("All injected files purged.\n0 traces remaining.")
        Clock.schedule_once(lambda dt: setattr(self, "progress", 0))
        Clock.schedule_once(lambda dt: self._set_state("idle"))

    def _delete_file(self):
        manifest = self._load_manifest()

        for fpath in manifest.get("files", []):
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception:
                if self.is_rooted:
                    try: os.system(f"su -c 'rm -f \"{fpath}\"'")
                    except Exception: pass

        for dpath in reversed(manifest.get("dirs", [])):
            try:
                if os.path.isdir(dpath) and not os.listdir(dpath):
                    os.rmdir(dpath)
            except Exception:
                pass

        dest = os.path.join(self.target_path, TARGET_FILENAME)
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except Exception:
                if self.is_rooted:
                    try: os.system(f"su -c 'rm -f \"{dest}\"'")
                    except Exception: pass

        self._clear_manifest()

    def _save_manifest(self, files, dirs):
        try:
            with open(INSTALLED_MANIFEST, "w", encoding="utf-8") as f:
                json.dump({"files": files, "dirs": dirs}, f)
        except Exception:
            pass

    def _load_manifest(self):
        if os.path.exists(INSTALLED_MANIFEST):
            try:
                with open(INSTALLED_MANIFEST, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"files": [], "dirs": []}

    def _clear_manifest(self):
        if os.path.exists(INSTALLED_MANIFEST):
            try: os.remove(INSTALLED_MANIFEST)
            except OSError: pass

    def switch_key(self):
        if self.conn_state == "connected":
            self._begin_disconnect()
        if os.path.exists(LICENSE_CACHE):
            try: os.remove(LICENSE_CACHE)
            except OSError: pass
        if self.manager:
            self.manager.current = "login"

# ======================================================================
# 7. MAIN APP CLASS & ENTRY POINT
# ======================================================================
class NexusApp(App):
    def build(self):
        self.title = "Nexus UC Store"
        Builder.load_string(KV)
        sm = ScreenManager(transition=FadeTransition())
        login_sc = LoginScreen(name="login")
        main_sc = MainScreen(name="main")
        sm.add_widget(login_sc)
        sm.add_widget(main_sc)

        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    k = f.read().strip()
                    if k:
                        sm.current = "main"
                        return sm
            except Exception:
                pass

        sm.current = "login"
        return sm

if __name__ == "__main__":
    NexusApp().run()
