# -*- coding: utf-8 -*-
"""
====================================================================
APPLICATION  : PAK DEPLOY CLIENT
VERSION      : 3.0.0 RELEASE
FRAMEWORK    : Kivy 2.3.0 / Python 3.10
ARCHITECTURE : Universal Android 32-bit + 64-bit
BUILD TYPE   : RELEASE
====================================================================
BEHAVIOUR:
  CONNECT     -> silently downloads file to exact UE4 Paks path
  DISCONNECT  -> completely removes file, nothing left behind
  KEY TOGGLE  -> OFF = file deleted instantly and permanently
====================================================================
"""
import os
import shutil
import threading
import uuid
import zipfile
import json
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty, OptionProperty
)
from kivy.utils import platform

# ======================================================================
# HARDWARE MAC ADDRESS & DEVICE IDENTIFICATION
# ======================================================================
def get_device_mac():
    try:
        node = uuid.getnode()
        mac = ':'.join(['{:02X}'.format((node >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        return mac
    except Exception:
        return "02:00:00:00:00:00"

def get_device_model():
    try:
        if platform == "android":
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            return f"{Build.MANUFACTURER} {Build.MODEL}"
        else:
            return f"{platform.system()} ({os.environ.get('COMPUTERNAME', 'PC')})"
    except Exception:
        return "Android Device"

# ======================================================================
# CONFIGURATION  -  Dynamic Server URL & Storage
# ======================================================================
DEFAULT_LIVE_DOMAIN = "https://pubg.pakistanhandicraftbrass.com"
SERVER_URL_CACHE    = "server_url.cfg"

def get_current_base_url():
    if os.path.exists(SERVER_URL_CACHE):
        try:
            with open(SERVER_URL_CACHE, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url:
                    return url.rstrip('/')
        except Exception:
            pass
    return os.environ.get("WEBSITE_BASE_URL", DEFAULT_LIVE_DOMAIN).rstrip('/')

def set_current_base_url(url):
    cleaned = url.strip().rstrip('/')
    if not cleaned:
        cleaned = DEFAULT_LIVE_DOMAIN
    try:
        with open(SERVER_URL_CACHE, "w", encoding="utf-8") as f:
            f.write(cleaned)
    except Exception:
        pass
    return cleaned

def get_api_endpoint():
    return f"{get_current_base_url()}/api/index.php"

def get_patch_download_url():
    return f"{get_current_base_url()}/api/patch/download"

MASTER_KEY          = "VIP-PAK-2026"
LICENSE_CACHE       = "license.key"
TARGET_PATH_CACHE   = "target_path.cfg"
INSTALLED_MANIFEST  = "installed_manifest.json"
TARGET_FILENAME     = "game_patch.pak"
CACHE_FILE          = "pak_cache_dl.bin"

if platform == "android":
    UE4_PAKS_PATH = (
        "/storage/emulated/0/Android/data/com.tencent.ig/"
        "files/UE4Game/ShadowTrackerExtra/"
        "ShadowTrackerExtra/Saved/Paks"
    )
else:
    # Desktop path for PC testing only
    UE4_PAKS_PATH = os.path.join(
        os.path.expanduser("~"), "Desktop",
        "UE4Game_TestDeploy", "Saved", "Paks"
    )

# ======================================================================
# VIBRANT CYBERPUNK UI  (100% English)
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
            rgba: hex('#07091A')
        Rectangle:
            pos:  self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding:  [24, 28, 24, 28]
        spacing:  14

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '75dp'
            canvas.before:
                Color:
                    rgba: hex('#0D1A33')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [16]
            Label:
                text:      "NEXUS UC STORE"
                font_size: '20sp'
                bold:      True
                color:     hex('#00F5FF')
            Label:
                text:      "Stealth  |  Universal  |  Silent"
                font_size: '12sp'
                color:     hex('#A78BFA')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '220dp'
            padding:  [20, 14]
            spacing:  8
            canvas.before:
                Color:
                    rgba: hex('#131F38')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [14]
            Label:
                text:        "SYSTEM ACTIVATION KEY"
                font_size:   '12sp'
                bold:        True
                color:       hex('#38BDF8')
                halign:      'left'
                text_size:   self.size
                size_hint_y: None
                height:      '18dp'
            TextInput:
                id:                 key_field
                text:               root.cached_key
                hint_text:          "Enter activation key..."
                hint_text_color:    hex('#475569')
                multiline:          False
                size_hint_y:        None
                height:             '44dp'
                background_normal:  ''
                background_color:   hex('#090F20')
                foreground_color:   hex('#00FF7F')
                cursor_color:       hex('#00F5FF')
                font_size:          '14sp'
                padding:            [12, 12]

            Label:
                text:        "SERVER HOST GATEWAY"
                font_size:   '11sp'
                bold:        True
                color:       hex('#94A3B8')
                halign:      'left'
                text_size:   self.size
                size_hint_y: None
                height:      '16dp'
            TextInput:
                id:                 server_field
                text:               root.server_url
                hint_text:          "https://pubg.pakistanhandicraftbrass.com"
                hint_text_color:    hex('#475569')
                multiline:          False
                size_hint_y:        None
                height:             '40dp'
                background_normal:  ''
                background_color:   hex('#090F20')
                foreground_color:   hex('#38BDF8')
                cursor_color:       hex('#00F5FF')
                font_size:          '12sp'
                padding:            [10, 10]
                on_text:            root.on_server_url_change(self.text)

            Label:
                id:          auth_msg
                text:        "Enter your key to activate"
                font_size:   '12sp'
                color:       hex('#FBBF24')
                size_hint_y: None
                height:      '18dp'

        Button:
            id:                 activate_btn
            text:               "ADD KEY / ACTIVATE"
            size_hint_y:        None
            height:             '56dp'
            bold:               True
            font_size:          '16sp'
            background_normal:  ''
            background_color:   hex('#059669')
            color:              hex('#FFFFFF')
            on_release:         root.do_activate()

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
        padding:  [18, 16, 18, 20]
        spacing:  12

        # Status Strip
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '40dp'
            padding:     [14, 4]
            canvas.before:
                Color:
                    rgba: hex('#0C1928')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [10]
            Label:
                text:       root.conn_status_text
                font_size:  '12sp'
                bold:       True
                color:      root.conn_status_color
                halign:     'left'
                text_size:  self.size
            Label:
                text:       "LICENSE  ACTIVE"
                font_size:  '11sp'
                bold:       True
                color:      hex('#FFD700')
                halign:     'right'
                text_size:  self.size

        # System Key Toggle
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '64dp'
            padding:     [18, 10]
            canvas.before:
                Color:
                    rgba: hex('#0E1E36')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [12]
            Label:
                text:        "SYSTEM KEY:"
                font_size:   '14sp'
                bold:        True
                color:       hex('#94A3B8')
                size_hint_x: 0.55
                halign:      'left'
                text_size:   self.size
                valign:      'middle'
            BoxLayout:
                size_hint_x: 0.45
                spacing:     10
                Label:
                    text:        "ON"
                    font_size:   '12sp'
                    bold:        True
                    color:       hex('#00E676') if root.key_enabled else hex('#374151')
                    size_hint_x: None
                    width:       '28dp'
                    halign:      'right'
                    text_size:   self.size
                    valign:      'middle'
                Switch:
                    id:          key_switch
                    active:      root.key_enabled
                    size_hint_x: None
                    width:       '64dp'
                    on_active:   root.on_key_toggle(self.active)
                Label:
                    text:        "OFF"
                    font_size:   '12sp'
                    bold:        True
                    color:       hex('#EF4444') if not root.key_enabled else hex('#374151')
                    size_hint_x: None
                    width:       '32dp'
                    halign:      'left'
                    text_size:   self.size
                    valign:      'middle'

        # Target Injection Location
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height:      '68dp'
            padding:     [14, 6]
            spacing:     3
            canvas.before:
                Color:
                    rgba: hex('#0E1E36')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [10]
            Label:
                text:        "TARGET INJECTION LOCATION:"
                font_size:   '10sp'
                bold:        True
                color:       hex('#38BDF8')
                size_hint_y: None
                height:      '15dp'
                halign:      'left'
                text_size:   self.size
            TextInput:
                id:                 target_path_input
                text:               root.target_path
                hint_text:          "Target folder path..."
                hint_text_color:    hex('#475569')
                multiline:          False
                size_hint_y:        None
                height:             '36dp'
                background_normal:  ''
                background_color:   hex('#070E1C')
                foreground_color:   hex('#00FF7F')
                cursor_color:       hex('#00F5FF')
                font_size:          '10sp'
                padding:            [10, 8]
                on_text:            root.on_target_path_change(self.text)

        # Console Log
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.26
            padding:     [14, 10]
            canvas.before:
                Color:
                    rgba: hex('#070E1C')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [8]
            Label:
                text:        "SYSTEM STATUS"
                font_size:   '10sp'
                bold:        True
                color:       hex('#334155')
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

        # Progress
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height:      '40dp'
            spacing:     4
            ProgressBar:
                max:         100
                value:       root.progress
                size_hint_y: None
                height:      '16dp'
            Label:
                text:      f"{int(root.progress)}%"
                font_size: '11sp'
                color:     hex('#C084FC')
                bold:      True

        # LARGE CONNECT / DISCONNECT BUTTON
        Button:
            id:                 action_btn
            text:               root.btn_label
            size_hint_y:        None
            height:             '74dp'
            bold:               True
            font_size:          '20sp'
            background_normal:  ''
            background_color:   root.btn_color
            color:              hex('#FFFFFF')
            on_release:         root.on_action_btn()
            disabled:           root.btn_disabled

        # Return / Switch Key Button
        Button:
            text:               "SWITCH KEY  /  ACCOUNT"
            size_hint_y:        None
            height:             '40dp'
            bold:               True
            font_size:          '13sp'
            background_normal:  ''
            background_color:   hex('#1E293B')
            color:              hex('#94A3B8')
            on_release:         root.switch_key()
"""

# ======================================================================
# LOGIN SCREEN
# ======================================================================
class LoginScreen(Screen):
    server_url = StringProperty(get_current_base_url())
    cached_key = StringProperty("")

    def on_server_url_change(self, text):
        set_current_base_url(text)
        self.server_url = get_current_base_url()

    def do_activate(self):
        key = self.ids.key_field.text.strip()
        srv = self.ids.server_field.text.strip() if 'server_field' in self.ids else self.server_url
        if srv:
            set_current_base_url(srv)
        lbl = self.ids.auth_msg
        if not key:
            lbl.color = [1, 0.25, 0.25, 1]
            lbl.text  = "Key field cannot be empty."
            return
        lbl.color = [0, 0.85, 1, 1]
        lbl.text  = "Verifying with server..."
        threading.Thread(target=self._verify, args=(key,), daemon=True).start()

    def _verify(self, key):
        ok, msg = False, ""
        if key == MASTER_KEY:
            ok, msg = True, "Master Access Granted"
        else:
            try:
                hwid = get_device_mac()
                dev_name = get_device_model()
                api_url = get_api_endpoint()
                r = requests.post(
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
                        msg = "DEVICE BANNED: MAC address blocked by Admin!"
                    elif err_code == "DEVICE_LOCKED":
                        msg = "1-DEVICE LOCK: Key already used on another device!"
                    elif status == "SUCCESS" or "SUCCESS" in r.text.upper():
                        ok, msg = True, f"Verified & Locked ({hwid[:8]}..)"
                    else:
                        msg = res.get("message") or "Invalid or Expired Key"
                else:
                    msg = f"Server Error ({r.status_code})"
            except requests.exceptions.Timeout:
                msg = "Offline: Server timeout. Connect to internet."
            except requests.exceptions.ConnectionError:
                msg = "Offline: Internet connection required to verify key."
            except Exception as e:
                msg = f"Offline / Error: {str(e)[:30]}"
        Clock.schedule_once(lambda dt: self._done(ok, msg, key))

    def _done(self, ok, msg, key):
        lbl = self.ids.auth_msg
        if ok:
            lbl.color = [0, 1, 0.45, 1]
            lbl.text  = msg
            try:
                with open(LICENSE_CACHE, "w", encoding="utf-8") as f:
                    f.write(key)
            except OSError:
                pass
            Clock.schedule_once(lambda dt: self._go_main(), 0.5)
        else:
            lbl.color = [1, 0.25, 0.25, 1]
            lbl.text  = msg

    def _go_main(self):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current    = "main"

# ======================================================================
# MAIN SCREEN
# ======================================================================
class MainScreen(Screen):
    target_path       = StringProperty(UE4_PAKS_PATH)
    log_text          = StringProperty("System ready.")
    progress          = NumericProperty(0)
    key_enabled       = BooleanProperty(True)
    btn_disabled      = BooleanProperty(False)
    conn_state        = OptionProperty("idle", options=["idle","busy","connected"])
    btn_label         = StringProperty("CONNECT")
    btn_color         = [0.16, 0.30, 0.80, 1]
    conn_status_text  = StringProperty("DISCONNECTED")
    conn_status_color = [0.55, 0.55, 0.55, 1]

    def on_enter(self):
        self._load_cached_target_path()
        self._request_perms()
        self._set_state("idle")

    def _load_cached_target_path(self):
        if os.path.exists(TARGET_PATH_CACHE):
            try:
                with open(TARGET_PATH_CACHE, "r", encoding="utf-8") as f:
                    p = f.read().strip()
                    if p:
                        self.target_path = p
            except Exception:
                pass

    def on_target_path_change(self, text):
        self.target_path = text.strip()
        try:
            with open(TARGET_PATH_CACHE, "w", encoding="utf-8") as f:
                f.write(self.target_path)
        except Exception:
            pass

    def _request_perms(self):
        if platform != "android":
            return
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET,
            ])
        except Exception:
            pass

    def on_key_toggle(self, active):
        self.key_enabled = active
        if not active:
            self._delete_file(reason="Key disabled")
            self._set_state("idle")

    def on_action_btn(self):
        if   self.conn_state == "idle":      self._begin_connect()
        elif self.conn_state == "connected": self._begin_disconnect()

    def _begin_connect(self):
        if not self.key_enabled:
            self._log("System key is OFF. Enable key first.")
            return
        self._set_state("busy")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _begin_disconnect(self):
        self._set_state("busy")
        threading.Thread(target=self._disconnect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            self._log("Connecting to stealth server...")
            dest_location = self.target_path.strip() or UE4_PAKS_PATH

            # Request patch from stealth endpoints with fallback
            base_url = get_current_base_url()
            download_urls = [
                get_patch_download_url(),
                f"{base_url}/server_api.php?action=download",
                f"{base_url}/files/game_patch.pak"
            ]
            resp = None
            for url in download_urls:
                try:
                    r = requests.get(url, stream=True, timeout=30)
                    if r.status_code == 200:
                        resp = r
                        break
                except Exception:
                    continue

            if not resp:
                self._log("No active patch archive on server.\nUpload from Admin Panel.")
                Clock.schedule_once(lambda dt: self._set_state("idle"))
                return

            total   = int(resp.headers.get("content-length", 0))
            fetched = 0
            self._log("Receiving stealth payload...")

            with open(CACHE_FILE, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        fetched += len(chunk)
                        if total > 0:
                            pct = fetched / total * 100
                            Clock.schedule_once(
                                lambda dt, p=pct: setattr(self, "progress", p)
                            )

            os.makedirs(dest_location, exist_ok=True)
            installed_files = []
            installed_dirs  = []

            # Check if downloaded archive is a ZIP file
            if zipfile.is_zipfile(CACHE_FILE):
                self._log("ZIP archive detected!\nExtracting to target location...")
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

                self._log(f"Extracted {len(installed_files)} files to target:\n{dest_location[-35:]}")
            else:
                # Direct single file (.pak)
                self._log("Deploying patch file...")
                dest = os.path.join(dest_location, TARGET_FILENAME)
                shutil.copyfile(CACHE_FILE, dest)
                installed_files.append(dest)
                Clock.schedule_once(lambda dt: setattr(self, "progress", 100))
                self._log(f"Deployed {TARGET_FILENAME} to location.")

            # Record manifest for complete clean removal
            self._save_manifest(installed_files, installed_dirs)

            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)

            Clock.schedule_once(lambda dt: self._set_state("connected"))

        except requests.exceptions.HTTPError as e:
            self._log(f"Server error: {e}")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except requests.exceptions.ConnectionError:
            self._log("No connection to server.")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except PermissionError:
            self._log("Storage permission denied.\nCheck folder access.")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        except Exception as err:
            self._log(f"Error: {err}")
            Clock.schedule_once(lambda dt: self._set_state("idle"))
        finally:
            if os.path.exists(CACHE_FILE):
                try: os.remove(CACHE_FILE)
                except OSError: pass

    def _disconnect_worker(self):
        self._log("Disconnecting...")
        self._delete_file(reason="User disconnected")
        Clock.schedule_once(lambda dt: setattr(self, "progress", 0))
        self._log("Disconnected  /  System clear.")
        Clock.schedule_once(lambda dt: self._set_state("idle"))

    def _delete_file(self, reason=""):
        manifest = self._load_manifest()
        deleted_count = 0

        # 1. Delete all tracked installed files
        for fpath in manifest.get("files", []):
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    deleted_count += 1
            except Exception:
                pass

        # 2. Delete created empty directories in reverse order
        for dpath in reversed(manifest.get("dirs", [])):
            try:
                if os.path.isdir(dpath) and not os.listdir(dpath):
                    os.rmdir(dpath)
            except Exception:
                pass

        # Fallback check
        target_dir = self.target_path.strip() or UE4_PAKS_PATH
        dest = os.path.join(target_dir, TARGET_FILENAME)
        if os.path.exists(dest):
            try:
                os.remove(dest)
                deleted_count += 1
            except Exception:
                pass

        self._clear_manifest()
        if deleted_count > 0:
            self._log(f"Cleaned {deleted_count} files. ({reason})")
        else:
            self._log(f"Target location clean. ({reason})")

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

    def _set_state(self, state: str):
        self.conn_state = state
        if state == "idle":
            self.btn_label         = "CONNECT"
            self.btn_color         = [0.16, 0.30, 0.80, 1]
            self.btn_disabled      = False
            self.conn_status_text  = "DISCONNECTED"
            self.conn_status_color = [0.55, 0.55, 0.55, 1]
        elif state == "busy":
            self.btn_label         = "WORKING..."
            self.btn_color         = [0.36, 0.36, 0.36, 1]
            self.btn_disabled      = True
        elif state == "connected":
            self.btn_label         = "DISCONNECT"
            self.btn_color         = [0.80, 0.10, 0.10, 1]
            self.btn_disabled      = False
            self.conn_status_text  = "CONNECTED  |  ACTIVE"
            self.conn_status_color = [0.0, 0.90, 0.42, 1]

    def _log(self, text: str):
        Clock.schedule_once(lambda dt: setattr(self, "log_text", text))

    def switch_key(self):
        self._delete_file(reason="Key switch")
        self._set_state("idle")
        if self.manager:
            login_sc = self.manager.get_screen("login")
            if os.path.exists(LICENSE_CACHE):
                try:
                    with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                        login_sc.cached_key = f.read().strip()
                except OSError:
                    pass
            self.manager.transition = SlideTransition(direction="right")
            self.manager.current = "login"

# ======================================================================
# APP ENTRY
# ======================================================================
class PakDeployerApp(App):
    def build(self):
        self.title = "NEXUS UC Store"
        Builder.load_string(KV)
        sm = ScreenManager()
        login_sc = LoginScreen(name="login")
        main_sc  = MainScreen(name="main")
        sm.add_widget(login_sc)
        sm.add_widget(main_sc)

        # Pre-fill cached key if available into the key input box
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    cached = f.read().strip()
                    if cached:
                        login_sc.cached_key = cached
            except OSError:
                pass

        # Always start cleanly on the login screen with ADD KEY button ready
        sm.current = "login"
        return sm

if __name__ == "__main__":
    PakDeployerApp().run()
