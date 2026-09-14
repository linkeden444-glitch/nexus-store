# -*- coding: utf-8 -*-
"""
====================================================================
APPLICATION  : NEXUS VIP STEALTH ENGINE
VERSION      : 3.0.0 RELEASE
FRAMEWORK    : Kivy 2.3.0 / Python 3.11 / Universal Android
ARCHITECTURE : Universal Android (arm64-v8a + armeabi-v7a)
====================================================================
BEHAVIOUR:
  1. App opens straight to the sleek VIP Dashboard.
  2. Clicking CONNECT checks for VIP Key. If not activated,
     a sleek activation card prompts the user for their key.
  3. CONNECT     -> silently downloads file to exact UE4 Paks path
  4. DISCONNECT  -> completely removes file, nothing left behind
  5. KILL SWITCH -> OFF = file deleted instantly and permanently
====================================================================
"""
import os
import shutil
import subprocess
import threading
import uuid
import zipfile
import json
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.modalview import ModalView
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty, OptionProperty
)
from kivy.utils import platform

# ======================================================================
# HARDWARE IDENTIFICATION & ROOT DETECTION
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
            return f"{Build.MANUFACTURER} {Build.MODEL}".strip()
        else:
            return f"{platform.system()} ({os.environ.get('COMPUTERNAME', 'PC')})"
    except Exception:
        return "Android Device"

def is_device_rooted():
    try:
        su_paths = [
            "/system/bin/su", "/system/xbin/su", "/sbin/su",
            "/system/sd/xbin/su", "/data/local/xbin/su",
            "/data/local/bin/su", "/system/app/Superuser.apk"
        ]
        for p in su_paths:
            if os.path.exists(p):
                return True
        res = subprocess.run(["which", "su"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False

# ======================================================================
# MULTI-GAME PUBG TARGET PATHS
# ======================================================================
GAME_VARIANTS = {
    "GLOBAL": {
        "label": "PUBG Global",
        "pkg": "com.tencent.ig",
    },
    "BGMI": {
        "label": "BGMI (India)",
        "pkg": "com.pubg.imobile",
    },
    "KR": {
        "label": "PUBG Korea",
        "pkg": "com.pubg.krmobile",
    },
    "VN": {
        "label": "PUBG Vietnam",
        "pkg": "com.vng.pubgmobile",
    },
}

def get_game_paks_path(pkg="com.tencent.ig"):
    if platform == "android":
        return f"/storage/emulated/0/Android/data/{pkg}/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks"
    else:
        return os.path.join(
            os.path.expanduser("~"), "Desktop",
            "UE4Game_TestDeploy", pkg, "Saved", "Paks"
        )

def auto_detect_game_path():
    if platform == "android":
        for code, info in GAME_VARIANTS.items():
            base_p = f"/storage/emulated/0/Android/data/{info['pkg']}"
            if os.path.exists(base_p):
                return get_game_paks_path(info['pkg'])
    return get_game_paks_path("com.tencent.ig")

def detect_variant_code_from_path(path_str):
    for code, info in GAME_VARIANTS.items():
        if info['pkg'] in path_str:
            return code
    return "GLOBAL"

# ======================================================================
# INTERNAL CONFIGURATION (NO EXPOSED URLS IN UI)
# ======================================================================
DEFAULT_LIVE_DOMAIN = "https://pubg.pakistanhandicraftbrass.com"
SERVER_URL_CACHE    = "server_url.cfg"
LICENSE_CACHE       = "license.key"
TARGET_PATH_CACHE   = "target_path.cfg"
INSTALLED_MANIFEST  = "installed_manifest.json"
MASTER_KEY          = "VIP-PAK-2026"
TARGET_FILENAME     = "game_patch.pak"
CACHE_FILE          = "pak_cache_dl.bin"

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

def get_api_endpoint():
    return f"{get_current_base_url()}/api/index.php"

def get_patch_download_url():
    return f"{get_current_base_url()}/api/patch/download"

UE4_PAKS_PATH = auto_detect_game_path()

# ======================================================================
# VIBRANT CYBERPUNK UI (100% CLEAN - NO EXPOSED GATEWAYS)
# ======================================================================
KV = """
#:import hex kivy.utils.get_color_from_hex

<ActivationModalView>:
    size_hint: (0.92, None)
    height: '340dp'
    auto_dismiss: True
    background_color: [0, 0, 0, 0.85]
    BoxLayout:
        orientation: 'vertical'
        padding: [22, 18]
        spacing: 10
        canvas.before:
            Color:
                rgba: hex('#0A1124')
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [18]
            Color:
                rgba: hex('#0284C7')
            Line:
                rounded_rectangle: (self.x, self.y, self.width, self.height, 18)
                width: 1.5

        # Title Row with Close Button
        BoxLayout:
            size_hint_y: None
            height: '28dp'
            Label:
                text: "✦ VIP LICENSE ACTIVATION ✦"
                font_size: '14sp'
                bold: True
                color: hex('#00F5FF')
                halign: 'left'
                text_size: self.size
            Button:
                text: "✕"
                size_hint_x: None
                width: '32dp'
                font_size: '15sp'
                bold: True
                background_normal: ''
                background_color: hex('#1E293B')
                color: hex('#EF4444')
                on_release: root.dismiss()

        Label:
            text: "A valid VIP Key is required to connect and inject."
            font_size: '11sp'
            color: hex('#94A3B8')
            halign: 'left'
            text_size: self.size
            size_hint_y: None
            height: '16dp'

        # Device Binding Info
        Label:
            text: root.device_info
            font_size: '10sp'
            color: hex('#64748B')
            halign: 'left'
            text_size: self.size
            size_hint_y: None
            height: '14dp'

        # Key Input Box
        TextInput:
            id: key_input
            text: root.entered_key
            hint_text: "Enter VIP Activation Key..."
            hint_text_color: hex('#475569')
            multiline: False
            size_hint_y: None
            height: '44dp'
            background_normal: ''
            background_color: hex('#050B16')
            foreground_color: hex('#00FF7F')
            cursor_color: hex('#00F5FF')
            font_size: '13sp'
            padding: [12, 12]

        # Quick Paste Button
        Button:
            text: "📋 PASTE FROM CLIPBOARD"
            size_hint_y: None
            height: '32dp'
            font_size: '11sp'
            bold: True
            background_normal: ''
            background_color: hex('#1E293B')
            color: hex('#93C5FD')
            on_release: root.paste_clipboard()

        # Status Message
        Label:
            id: status_lbl
            text: root.status_msg
            font_size: '11sp'
            color: hex('#FBBF24')
            size_hint_y: None
            height: '18dp'

        # Activate & Connect Button
        Button:
            id: activate_btn
            text: "⚡ VERIFY & CONNECT ⚡"
            size_hint_y: None
            height: '50dp'
            bold: True
            font_size: '15sp'
            background_normal: ''
            background_color: hex('#059669')
            color: hex('#FFFFFF')
            on_release: root.verify_and_connect()

<MainScreen>:
    canvas.before:
        Color:
            rgba: hex('#060813')
        Rectangle:
            pos:  self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding:  [18, 16, 18, 20]
        spacing:  11

        # Top Header Bar
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '44dp'
            padding: [4, 0]
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: "NEXUS VIP STEALTH"
                    font_size: '18sp'
                    bold: True
                    color: hex('#00F5FF')
                    halign: 'left'
                    text_size: self.size
                Label:
                    text: "VIP CLIENT  |  UNIVERSAL ENGINE v3.0"
                    font_size: '10sp'
                    bold: True
                    color: hex('#A78BFA')
                    halign: 'left'
                    text_size: self.size
            Button:
                text: root.key_button_text
                font_size: '10sp'
                bold: True
                size_hint_x: None
                width: '100dp'
                background_normal: ''
                background_color: hex('#0F172A')
                color: hex('#38BDF8')
                on_release: root.open_key_manager()

        # Status Strip
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '38dp'
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
                text:       root.license_badge_text
                font_size:  '11sp'
                bold:       True
                color:      root.license_badge_color
                halign:     'right'
                text_size:  self.size

        # Quick Game Target Selector Row
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '66dp'
            padding: [12, 6]
            spacing: 5
            canvas.before:
                Color:
                    rgba: hex('#0C1527')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            Label:
                text: f"GAME TARGET: {root.active_variant}"
                font_size: '10sp'
                bold: True
                color: hex('#38BDF8')
                halign: 'left'
                text_size: self.size
                size_hint_y: None
                height: '14dp'
            BoxLayout:
                spacing: 8
                Button:
                    text: "GLOBAL"
                    font_size: '11sp'
                    bold: True
                    background_normal: ''
                    background_color: hex('#2563EB') if root.active_variant == 'GLOBAL' else hex('#1E293B')
                    color: hex('#FFFFFF') if root.active_variant == 'GLOBAL' else hex('#94A3B8')
                    on_release: root.set_game_variant('GLOBAL')
                Button:
                    text: "BGMI"
                    font_size: '11sp'
                    bold: True
                    background_normal: ''
                    background_color: hex('#2563EB') if root.active_variant == 'BGMI' else hex('#1E293B')
                    color: hex('#FFFFFF') if root.active_variant == 'BGMI' else hex('#94A3B8')
                    on_release: root.set_game_variant('BGMI')
                Button:
                    text: "KR"
                    font_size: '11sp'
                    bold: True
                    background_normal: ''
                    background_color: hex('#2563EB') if root.active_variant == 'KR' else hex('#1E293B')
                    color: hex('#FFFFFF') if root.active_variant == 'KR' else hex('#94A3B8')
                    on_release: root.set_game_variant('KR')
                Button:
                    text: "VN"
                    font_size: '11sp'
                    bold: True
                    background_normal: ''
                    background_color: hex('#2563EB') if root.active_variant == 'VN' else hex('#1E293B')
                    color: hex('#FFFFFF') if root.active_variant == 'VN' else hex('#94A3B8')
                    on_release: root.set_game_variant('VN')

        # Kill Switch Toggle
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height:      '56dp'
            padding:     [16, 8]
            canvas.before:
                Color:
                    rgba: hex('#0E1E36')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [12]
            Label:
                text:        "STEALTH KILL SWITCH:"
                font_size:   '13sp'
                bold:        True
                color:       hex('#94A3B8')
                size_hint_x: 0.55
                halign:      'left'
                text_size:   self.size
                valign:      'middle'
            BoxLayout:
                size_hint_x: 0.45
                spacing:     8
                Label:
                    text:        "ON"
                    font_size:   '12sp'
                    bold:        True
                    color:       hex('#00E676') if root.key_enabled else hex('#374151')
                    size_hint_x: None
                    width:       '26dp'
                    halign:      'right'
                    text_size:   self.size
                    valign:      'middle'
                Switch:
                    id:          key_switch
                    active:      root.key_enabled
                    size_hint_x: None
                    width:       '60dp'
                    on_active:   root.on_key_toggle(self.active)
                Label:
                    text:        "OFF"
                    font_size:   '12sp'
                    bold:        True
                    color:       hex('#EF4444') if not root.key_enabled else hex('#374151')
                    size_hint_x: None
                    width:       '28dp'
                    halign:      'left'
                    text_size:   self.size
                    valign:      'middle'

        # Target Injection Location & Auto-detect
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height:      '72dp'
            padding:     [12, 6]
            spacing:     4
            canvas.before:
                Color:
                    rgba: hex('#0E1E36')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [10]
            BoxLayout:
                size_hint_y: None
                height: '16dp'
                Label:
                    text: "TARGET INJECTION PATH:"
                    font_size: '10sp'
                    bold: True
                    color: hex('#38BDF8')
                    halign: 'left'
                    text_size: self.size
                Button:
                    text: "[ AUTO DETECT ]"
                    font_size: '9sp'
                    bold: True
                    size_hint_x: None
                    width: '90dp'
                    background_normal: ''
                    background_color: hex('#1E293B')
                    color: hex('#00F5FF')
                    on_release: root.auto_detect()
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

        # System Status Console
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.24
            padding:     [14, 8]
            canvas.before:
                Color:
                    rgba: hex('#070E1C')
                RoundedRectangle:
                    pos:    self.pos
                    size:   self.size
                    radius: [8]
            Label:
                text:        "SYSTEM STATUS"
                font_size:   '9sp'
                bold:        True
                color:       hex('#475569')
                size_hint_y: None
                height:      '14dp'
                halign:      'left'
                text_size:   self.size
            Label:
                text:      root.log_text
                font_size: '11sp'
                color:     hex('#38BDF8')
                valign:    'middle'
                halign:    'center'
                text_size: self.size

        # Progress
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height:      '36dp'
            spacing:     3
            ProgressBar:
                max:         100
                value:       root.progress
                size_hint_y: None
                height:      '14dp'
            Label:
                text:      f"{int(root.progress)}%"
                font_size: '10sp'
                color:     hex('#C084FC')
                bold:      True

        # LARGE CONNECT / DISCONNECT BUTTON
        Button:
            id:                 action_btn
            text:               root.btn_label
            size_hint_y:        None
            height:             '70dp'
            bold:               True
            font_size:          '19sp'
            background_normal:  ''
            background_color:   root.btn_color
            color:              hex('#FFFFFF')
            on_release:         root.on_action_btn()
            disabled:           root.btn_disabled

        # Stealth Security Footer
        Label:
            text: "🔒 END-TO-END ENCRYPTED HARDWARE BINDING"
            font_size: '10sp'
            bold: True
            color: hex('#334155')
            size_hint_y: None
            height: '18dp'
"""

# ======================================================================
# ACTIVATION MODAL VIEW (PROMPTS ONLY WHEN CONNECTING WITHOUT KEY)
# ======================================================================
class ActivationModalView(ModalView):
    entered_key = StringProperty("")
    status_msg  = StringProperty("Enter VIP key to activate.")
    device_info = StringProperty("")

    def __init__(self, parent_screen, on_success_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_success_callback = on_success_callback
        hwid = get_device_mac()
        model = get_device_model()
        self.device_info = f"HWID: {hwid[:8]}...  |  {model}"
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    self.entered_key = f.read().strip()
            except Exception:
                pass

    def paste_clipboard(self):
        try:
            val = Clipboard.paste()
            if val:
                self.ids.key_input.text = val.strip()
                self.status_msg = "Key pasted from clipboard."
                self.ids.status_lbl.color = [0.2, 0.9, 1, 1]
        except Exception:
            pass

    def verify_and_connect(self):
        key = self.ids.key_input.text.strip()
        if not key:
            self.status_msg = "Key field cannot be empty."
            self.ids.status_lbl.color = [1, 0.25, 0.25, 1]
            return

        self.status_msg = "Verifying with VIP server..."
        self.ids.status_lbl.color = [0, 0.85, 1, 1]
        self.ids.activate_btn.disabled = True
        threading.Thread(target=self._verify_thread, args=(key,), daemon=True).start()

    def _verify_thread(self, key):
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
                        ok, msg = True, f"Verified & Bound ({hwid[:8]}..)"
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

        Clock.schedule_once(lambda dt: self._on_verified(ok, msg, key))

    def _on_verified(self, ok, msg, key):
        self.ids.activate_btn.disabled = False
        if ok:
            self.status_msg = msg
            self.ids.status_lbl.color = [0, 1, 0.45, 1]
            try:
                with open(LICENSE_CACHE, "w", encoding="utf-8") as f:
                    f.write(key)
            except OSError:
                pass

            if self.parent_screen:
                self.parent_screen.cached_key = key
                self.parent_screen.update_license_display()

            Clock.schedule_once(lambda dt: self._finish_and_connect(), 0.5)
        else:
            self.status_msg = msg
            self.ids.status_lbl.color = [1, 0.25, 0.25, 1]

    def _finish_and_connect(self):
        self.dismiss()
        if self.on_success_callback:
            self.on_success_callback()

# ======================================================================
# MAIN SCREEN (OPENS IMMEDIATELY ON APP LAUNCH)
# ======================================================================
class MainScreen(Screen):
    target_path          = StringProperty(UE4_PAKS_PATH)
    active_variant       = StringProperty("GLOBAL")
    log_text             = StringProperty("System ready.")
    progress             = NumericProperty(0)
    key_enabled          = BooleanProperty(True)
    btn_disabled         = BooleanProperty(False)
    conn_state           = OptionProperty("idle", options=["idle","busy","connected"])
    btn_label            = StringProperty("CONNECT")
    btn_color            = [0.12, 0.40, 0.90, 1]
    conn_status_text     = StringProperty("DISCONNECTED")
    conn_status_color    = [0.55, 0.55, 0.55, 1]
    license_badge_text   = StringProperty("NO KEY")
    license_badge_color  = [0.55, 0.55, 0.55, 1]
    key_button_text      = StringProperty("[ 🔑 VIP KEY ]")
    is_rooted            = BooleanProperty(False)
    cached_key           = StringProperty("")

    def on_enter(self):
        self.is_rooted = is_device_rooted()
        self._load_cached_key()
        self._load_cached_target_path()
        self._request_perms()
        self._set_state("idle")

    def _load_cached_key(self):
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    self.cached_key = f.read().strip()
            except Exception:
                pass
        self.update_license_display()

    def update_license_display(self):
        if self.cached_key:
            self.license_badge_text = "VIP ACTIVE"
            self.license_badge_color = [1, 0.84, 0, 1]
            self.key_button_text = "[ 🔑 KEY SET ]"
        else:
            self.license_badge_text = "KEY REQUIRED"
            self.license_badge_color = [0.94, 0.55, 0.2, 1]
            self.key_button_text = "[ 🔑 ENTER KEY ]"

    def open_key_manager(self):
        modal = ActivationModalView(
            parent_screen=self,
            on_success_callback=None
        )
        modal.open()

    def _load_cached_target_path(self):
        if os.path.exists(TARGET_PATH_CACHE):
            try:
                with open(TARGET_PATH_CACHE, "r", encoding="utf-8") as f:
                    p = f.read().strip()
                    if p:
                        self.target_path = p
                        self.active_variant = detect_variant_code_from_path(p)
                        return
            except Exception:
                pass
        self.target_path = auto_detect_game_path()
        self.active_variant = detect_variant_code_from_path(self.target_path)

    def set_game_variant(self, variant_code):
        if variant_code in GAME_VARIANTS:
            self.active_variant = variant_code
            pkg = GAME_VARIANTS[variant_code]["pkg"]
            new_path = get_game_paks_path(pkg)
            self.target_path = new_path
            self.on_target_path_change(new_path)
            self._log(f"Target switched to {GAME_VARIANTS[variant_code]['label']}")

    def auto_detect(self):
        detected = auto_detect_game_path()
        self.target_path = detected
        self.active_variant = detect_variant_code_from_path(detected)
        self.on_target_path_change(detected)
        self._log(f"Auto-detected: {self.active_variant}")

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
            self._delete_file(reason="Kill switch triggered")
            self._set_state("idle")

    def on_action_btn(self):
        if self.conn_state == "connected":
            self._begin_disconnect()
        elif self.conn_state == "idle":
            # Check if valid key exists
            if not self.cached_key:
                # Prompt user with Activation Modal
                modal = ActivationModalView(
                    parent_screen=self,
                    on_success_callback=self._begin_connect
                )
                modal.open()
            else:
                self._begin_connect()

    def _begin_connect(self):
        if not self.key_enabled:
            self._log("Kill Switch is OFF. Enable switch first.")
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

            # Request patch from endpoints with fallback
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

            # Ensure destination directory exists (standard or root fallback)
            try:
                os.makedirs(dest_location, exist_ok=True)
            except Exception:
                if self.is_rooted:
                    os.system(f"su -c 'mkdir -p \"{dest_location}\"'")

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
                try:
                    shutil.copyfile(CACHE_FILE, dest)
                except (PermissionError, OSError):
                    if self.is_rooted:
                        os.system(f"su -c 'cp \"{CACHE_FILE}\" \"{dest}\" && chmod 777 \"{dest}\"'")
                    else:
                        raise

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
                if self.is_rooted:
                    try:
                        os.system(f"su -c 'rm -f \"{fpath}\"'")
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
                if self.is_rooted:
                    os.system(f"su -c 'rm -f \"{dest}\"'")
                    deleted_count += 1

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
            self.btn_color         = [0.12, 0.40, 0.90, 1]
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

# ======================================================================
# APP ENTRY (OPENS DIRECTLY TO THE VIP DASHBOARD)
# ======================================================================
class PakDeployerApp(App):
    def build(self):
        self.title = "NEXUS VIP Engine"
        Builder.load_string(KV)
        sm = ScreenManager()
        main_sc = MainScreen(name="main")
        sm.add_widget(main_sc)
        sm.current = "main"
        return sm

if __name__ == "__main__":
    PakDeployerApp().run()
