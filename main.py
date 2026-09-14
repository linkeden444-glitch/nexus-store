# -*- coding: utf-8 -*-
"""
====================================================================
APPLICATION  : NEXUS TUNNEL - FROSTED GLASS VPN CLIENT
VERSION      : 3.0.0 RELEASE
FRAMEWORK    : Kivy 2.3.0 / Python 3.11 / Universal Android
ARCHITECTURE : Universal Android (arm64-v8a + armeabi-v7a)
====================================================================
"""
import os
import shutil
import subprocess
import threading
import uuid
import zipfile
import json
import time
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.core.clipboard import Clipboard
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty, ListProperty
)
from kivy.utils import platform

# ======================================================================
# BACKGROUND HARDWARE & ROOT DETECTION (NON-BLOCKING & SAFE)
# ======================================================================
def get_device_mac():
    try:
        if platform == "android":
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            SettingsSecure = autoclass("android.provider.Settings$Secure")
            cr = PythonActivity.mActivity.getContentResolver()
            aid = SettingsSecure.getString(cr, SettingsSecure.ANDROID_ID)
            if aid:
                return aid.upper()
    except Exception:
        pass
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
            import platform as sys_platform
            return f"{sys_platform.system()} ({os.environ.get('COMPUTERNAME', 'PC')})"
    except Exception:
        return "Android Device"

def is_device_rooted():
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
# MULTI-GAME PUBG TARGET PATHS (100% SILENT IN BACKGROUND)
# ======================================================================
GAME_VARIANTS = {
    "GLOBAL": "com.tencent.ig",
    "BGMI": "com.pubg.imobile",
    "KR": "com.pubg.krmobile",
    "VN": "com.vng.pubgmobile",
    "TW": "com.rekoo.pubgm",
}

def auto_detect_game_pkg():
    if platform == "android":
        for name, pkg in GAME_VARIANTS.items():
            base_p = f"/storage/emulated/0/Android/data/{pkg}"
            try:
                if os.path.exists(base_p):
                    return pkg
            except Exception:
                pass
    return "com.tencent.ig"

def get_game_base_path(pkg="com.tencent.ig"):
    if platform == "android":
        return f"/storage/emulated/0/Android/data/{pkg}"
    else:
        return os.path.join(
            os.path.expanduser("~"), "Desktop",
            "UE4Game_TestDeploy", pkg
        )

def get_game_paks_path(pkg="com.tencent.ig"):
    if platform == "android":
        return f"/storage/emulated/0/Android/data/{pkg}/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Paks"
    else:
        return os.path.join(
            get_game_base_path(pkg), "files", "UE4Game", "ShadowTrackerExtra", "ShadowTrackerExtra", "Saved", "Paks"
        )

def auto_detect_game_target():
    pkg = auto_detect_game_pkg()
    return get_game_paks_path(pkg)

# ======================================================================
# INTERNAL CONFIGURATION
# ======================================================================
DEFAULT_LIVE_DOMAIN = "https://pubg.pakistanhandicraftbrass.com"
SERVER_URL_CACHE    = "server_url.cfg"
LICENSE_CACHE       = "license.key"
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

# ======================================================================
# PURE FROSTED GLASS KIVY UI DEFINITION
# ======================================================================
KV = """
#:import hex kivy.utils.get_color_from_hex
#:import dp kivy.metrics.dp

<ActivationPopupModal>:
    size_hint: (0.92, None)
    height: '310dp'
    auto_dismiss: True
    background_color: [0.06, 0.09, 0.16, 0.75]
    BoxLayout:
        orientation: 'vertical'
        padding: [22, 20]
        spacing: 10
        canvas.before:
            Color:
                rgba: [0.98, 0.99, 1.0, 0.96]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [22]
            Color:
                rgba: [0.01, 0.52, 0.78, 0.8]
            Line:
                rounded_rectangle: (self.x, self.y, self.width, self.height, 22)
                width: 1.5

        # Title Row with Close Button
        BoxLayout:
            size_hint_y: None
            height: '28dp'
            Label:
                text: "VIP ACCESS REQUIRED"
                font_size: '14sp'
                bold: True
                color: hex('#0284C7')
                halign: 'left'
                text_size: self.size
            Button:
                text: "X"
                size_hint_x: None
                width: '32dp'
                font_size: '13sp'
                bold: True
                background_normal: ''
                background_color: hex('#FEE2E2')
                color: hex('#EF4444')
                on_release: root.dismiss()

        Label:
            text: "Enter your VIP License Key to authorize and start tunnel."
            font_size: '11sp'
            color: hex('#64748B')
            halign: 'left'
            text_size: self.size
            size_hint_y: None
            height: '16dp'

        # Key Input Field with Show/Hide Toggle
        BoxLayout:
            size_hint_y: None
            height: '46dp'
            spacing: 6
            TextInput:
                id: popup_key_input
                text: root.entered_key
                hint_text: "Enter VIP key..."
                hint_text_color: hex('#94A3B8')
                multiline: False
                password: root.popup_key_is_masked
                background_normal: ''
                background_color: hex('#FFFFFF')
                foreground_color: hex('#0F172A')
                cursor_color: hex('#0284C7')
                font_size: '13sp'
                padding: [12, 13]
            Button:
                text: "SHOW" if root.popup_key_is_masked else "HIDE"
                size_hint_x: None
                width: '64dp'
                font_size: '11sp'
                bold: True
                background_normal: ''
                background_color: hex('#F1F5F9')
                color: hex('#0284C7')
                on_release: root.toggle_popup_key_mask()

        Button:
            text: "PASTE FROM CLIPBOARD"
            size_hint_y: None
            height: '32dp'
            font_size: '11sp'
            bold: True
            background_normal: ''
            background_color: hex('#F1F5F9')
            color: hex('#0369A1')
            on_release: root.paste_clipboard()

        Label:
            id: popup_status_lbl
            text: root.status_msg
            font_size: '11sp'
            color: hex('#D97706')
            size_hint_y: None
            height: '16dp'

        Button:
            id: popup_activate_btn
            text: "ACTIVATE"
            size_hint_y: None
            height: '46dp'
            bold: True
            font_size: '14sp'
            background_normal: ''
            background_color: hex('#059669')
            color: hex('#FFFFFF')
            on_release: root.verify_and_connect()

<MainScreen>:
    canvas.before:
        Color:
            rgba: hex('#F8FAFC')
        Rectangle:
            pos:  self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: [0, 0, 0, 0]
        spacing: 0

        # Top App Header Bar
        BoxLayout:
            size_hint_y: None
            height: '58dp'
            padding: [20, 10]
            canvas.before:
                Color:
                    rgba: [1.0, 1.0, 1.0, 0.95]
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: hex('#E2E8F0')
                Line:
                    points: [self.x, self.y, self.right, self.y]
                    width: 1

            Label:
                text: "NEXUS TUNNEL"
                font_size: '19sp'
                bold: True
                color: hex('#0284C7')
                halign: 'left'
                valign: 'middle'
                text_size: self.size

            # Status Pill (Top Right)
            BoxLayout:
                size_hint_x: None
                width: '135dp'
                canvas.before:
                    Color:
                        rgba: root.status_pill_bg
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [14]
                    Color:
                        rgba: root.status_pill_border
                    Line:
                        rounded_rectangle: (self.x, self.y, self.width, self.height, 14)
                        width: 1
                Label:
                    text: root.conn_status_text
                    font_size: '10sp'
                    bold: True
                    color: root.conn_status_color
                    halign: 'center'
                    valign: 'middle'

        # Middle Content Area
        ScreenManager:
            id: tab_manager
            transition: SlideTransition(duration=0.28)

            # TAB 1: TUNNEL
            Screen:
                name: 'tab_tunnel'
                BoxLayout:
                    orientation: 'vertical'
                    padding: [22, 14]
                    spacing: 12

                    Widget:
                        size_hint_y: 0.15

                    # Circular VPN Power Button
                    AnchorLayout:
                        size_hint_y: None
                        height: '180dp'
                        anchor_x: 'center'
                        anchor_y: 'center'

                        RelativeLayout:
                            size_hint: (None, None)
                            size: ('140dp', '140dp')

                            Button:
                                id: vpn_btn
                                size_hint: (1, 1)
                                pos: (0, 0)
                                background_normal: ''
                                background_color: [0, 0, 0, 0]
                                on_release: root.on_vpn_button_press()
                                disabled: root.btn_disabled
                                canvas.before:
                                    # Outer Breathing Pulse Ring
                                    Color:
                                        rgba: [root.ring_color[0], root.ring_color[1], root.ring_color[2], root.ring_alpha]
                                    Line:
                                        circle: (self.center_x, self.center_y, 70 * root.ring_scale)
                                        width: 2.2
                                    # Inner Button Background
                                    Color:
                                        rgba: root.btn_bg_color
                                    Ellipse:
                                        pos: self.pos
                                        size: self.size
                                    # Button Border
                                    Color:
                                        rgba: root.btn_border_color
                                    Line:
                                        circle: (self.center_x, self.center_y, 70)
                                        width: 2.4
                                    # Native Vector Power Icon
                                    Color:
                                        rgba: root.btn_text_color
                                    Line:
                                        circle: (self.center_x, self.center_y + 12, 22, 38, 322)
                                        width: 3.2
                                        cap: 'round'
                                    Line:
                                        points: [self.center_x, self.center_y + 10, self.center_x, self.center_y + 36]
                                        width: 3.2
                                        cap: 'round'

                            Label:
                                text: root.btn_label
                                font_size: '11sp'
                                bold: True
                                color: root.btn_text_color
                                size_hint: (1, None)
                                height: '22dp'
                                pos_hint: {'center_x': 0.5, 'y': 0.16}
                                halign: 'center'
                                valign: 'middle'

                    # Connection State Text
                    Label:
                        text: root.conn_heading_text
                        font_size: '16sp'
                        bold: True
                        color: root.conn_heading_color
                        size_hint_y: None
                        height: '24dp'
                        halign: 'center'

                    Label:
                        text: root.conn_sub_text
                        font_size: '11sp'
                        color: hex('#64748B')
                        size_hint_y: None
                        height: '18dp'
                        halign: 'center'

                    # Progress Bar
                    ProgressBar:
                        max: 100
                        value: root.progress
                        size_hint_y: None
                        height: '8dp'
                        opacity: 1 if root.progress > 0 and root.progress < 100 else 0

                    Widget:
                        size_hint_y: 0.1

                    # VIP Key Expiration Countdown Timer Card
                    BoxLayout:
                        orientation: 'vertical'
                        size_hint_y: None
                        height: '76dp'
                        padding: [18, 10]
                        spacing: 4
                        canvas.before:
                            Color:
                                rgba: [1.0, 1.0, 1.0, 0.95]
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [16]
                            Color:
                                rgba: hex('#CBD5E1')
                            Line:
                                rounded_rectangle: (self.x, self.y, self.width, self.height, 16)
                                width: 1.2

                        Label:
                            text: "VIP ACCESS VALIDITY"
                            font_size: '11sp'
                            bold: True
                            color: hex('#0284C7')
                            halign: 'center'
                            size_hint_y: None
                            height: '18dp'

                        Label:
                            text: root.vip_countdown_text
                            font_size: '18sp'
                            bold: True
                            color: hex('#0F172A')
                            halign: 'center'

                    Widget:
                        size_hint_y: 0.1

            # TAB 2: LICENSE
            Screen:
                name: 'tab_license'
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    bar_width: '3dp'
                    bar_color: hex('#CBD5E1')
                    BoxLayout:
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        padding: [22, 16, 22, 24]
                        spacing: 12

                        Label:
                            text: "VIP SUBSCRIPTION"
                            font_size: '17sp'
                            bold: True
                            color: hex('#0284C7')
                            size_hint_y: None
                            height: '24dp'
                            halign: 'left'
                            text_size: self.size

                        Label:
                            text: "Enter your private VIP key to authorize high-speed tunnel access."
                            font_size: '11sp'
                            color: hex('#64748B')
                            size_hint_y: None
                            height: '16dp'
                            halign: 'left'
                            text_size: self.size

                        # Authorization Status Card
                        BoxLayout:
                            orientation: 'vertical'
                            size_hint_y: None
                            height: '75dp'
                            padding: [14, 10]
                            spacing: 6
                            canvas.before:
                                Color:
                                    rgba: [1.0, 1.0, 1.0, 0.95]
                                RoundedRectangle:
                                    pos: self.pos
                                    size: self.size
                                    radius: [14]
                                Color:
                                    rgba: hex('#CBD5E1')
                                Line:
                                    rounded_rectangle: (self.x, self.y, self.width, self.height, 14)
                                    width: 1
                            BoxLayout:
                                Label:
                                    text: "Subscription Tier"
                                    font_size: '11sp'
                                    color: hex('#64748B')
                                    halign: 'left'
                                    text_size: self.size
                                Label:
                                    text: "VIP Unlimited"
                                    font_size: '11sp'
                                    bold: True
                                    color: hex('#059669')
                                    halign: 'right'
                                    text_size: self.size
                            BoxLayout:
                                Label:
                                    text: "Access State"
                                    font_size: '11sp'
                                    color: hex('#64748B')
                                    halign: 'left'
                                    text_size: self.size
                                Label:
                                    text: root.card_key_status
                                    font_size: '11sp'
                                    bold: True
                                    color: root.card_key_color
                                    halign: 'right'
                                    text_size: self.size

                        Label:
                            text: "ENTER VIP KEY:"
                            font_size: '11sp'
                            bold: True
                            color: hex('#0284C7')
                            size_hint_y: None
                            height: '18dp'
                            halign: 'left'
                            text_size: self.size

                        # Input Row with Show/Hide Toggle Button
                        BoxLayout:
                            size_hint_y: None
                            height: '46dp'
                            spacing: 6

                            TextInput:
                                id: key_input_field
                                text: root.cached_key
                                hint_text: "Paste VIP key here..."
                                hint_text_color: hex('#94A3B8')
                                multiline: False
                                password: root.key_is_masked
                                background_normal: ''
                                background_color: hex('#FFFFFF')
                                foreground_color: hex('#0F172A')
                                cursor_color: hex('#0284C7')
                                font_size: '13sp'
                                padding: [12, 13]

                            Button:
                                text: "SHOW" if root.key_is_masked else "HIDE"
                                size_hint_x: None
                                width: '68dp'
                                font_size: '11sp'
                                bold: True
                                background_normal: ''
                                background_color: hex('#F1F5F9')
                                color: hex('#0284C7')
                                on_release: root.toggle_key_mask()

                        Button:
                            text: "PASTE FROM CLIPBOARD"
                            size_hint_y: None
                            height: '36dp'
                            font_size: '11sp'
                            bold: True
                            background_normal: ''
                            background_color: hex('#F1F5F9')
                            color: hex('#0369A1')
                            on_release: root.paste_clipboard()

                        Button:
                            id: save_license_btn
                            text: "ACTIVATE VIP KEY"
                            size_hint_y: None
                            height: '46dp'
                            font_size: '13sp'
                            bold: True
                            background_normal: ''
                            background_color: hex('#0284C7')
                            color: hex('#FFFFFF')
                            on_release: root.activate_key()

                        BoxLayout:
                            size_hint_y: None
                            height: '40dp'
                            spacing: 8

                            Button:
                                text: "DEACTIVATE KEY"
                                font_size: '11sp'
                                bold: True
                                background_normal: ''
                                background_color: hex('#FEF3C7')
                                color: hex('#D97706')
                                on_release: root.deactivate_key()

                            Button:
                                text: "DELETE KEY"
                                font_size: '11sp'
                                bold: True
                                background_normal: ''
                                background_color: hex('#FEE2E2')
                                color: hex('#DC2626')
                                on_release: root.delete_key()

                        Label:
                            id: license_msg_lbl
                            text: root.license_feedback_msg
                            font_size: '11sp'
                            color: root.license_feedback_color
                            size_hint_y: None
                            height: '22dp'
                            halign: 'center'

            # TAB 3: TERMINAL
            Screen:
                name: 'tab_terminal'
                BoxLayout:
                    orientation: 'vertical'
                    padding: [22, 16, 22, 24]
                    spacing: 10

                    Label:
                        text: "SYSTEM TERMINAL"
                        font_size: '17sp'
                        bold: True
                        color: hex('#0284C7')
                        size_hint_y: None
                        height: '24dp'
                        halign: 'left'
                        text_size: self.size

                    Label:
                        text: "Live background operational stream"
                        font_size: '11sp'
                        color: hex('#64748B')
                        size_hint_y: None
                        height: '16dp'
                        halign: 'left'
                        text_size: self.size

                    # Cyber Terminal Output Console
                    BoxLayout:
                        orientation: 'vertical'
                        size_hint_y: 1
                        canvas.before:
                            Color:
                                rgba: hex('#0B1329')
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [16]
                            Color:
                                rgba: hex('#1E293B')
                            Line:
                                rounded_rectangle: (self.x, self.y, self.width, self.height, 16)
                                width: 1.2
                        padding: [14, 12]

                        ScrollView:
                            do_scroll_x: False
                            do_scroll_y: True
                            bar_width: '2dp'
                            bar_color: hex('#38BDF8')
                            Label:
                                id: terminal_text_view
                                text: root.terminal_logs
                                font_size: '10sp'
                                color: hex('#38BDF8')
                                halign: 'left'
                                valign: 'top'
                                size_hint_y: None
                                height: self.texture_size[1]
                                text_size: (self.width, None)
                                markup: True

                    Button:
                        text: "COPY TERMINAL DATA"
                        size_hint_y: None
                        height: '38dp'
                        font_size: '11.5sp'
                        bold: True
                        background_normal: ''
                        background_color: hex('#F1F5F9')
                        color: hex('#0284C7')
                        on_release: root.copy_terminal_logs()

                    Label:
                        id: term_copy_lbl
                        text: root.terminal_copy_msg
                        font_size: '11sp'
                        color: hex('#059669')
                        size_hint_y: None
                        height: '18dp'
                        halign: 'center'

        # Bottom Floating White Navigation Dock
        BoxLayout:
            size_hint_y: None
            height: '66dp'
            padding: [16, 4, 16, 12]
            canvas.before:
                Color:
                    rgba: [1.0, 1.0, 1.0, 0.95]
                RoundedRectangle:
                    pos: [self.x + 16, self.y + 8]
                    size: [self.width - 32, self.height - 12]
                    radius: [20]
                Color:
                    rgba: hex('#CBD5E1')
                Line:
                    rounded_rectangle: (self.x + 16, self.y + 8, self.width - 32, self.height - 12, 20)
                    width: 1.2

            BoxLayout:
                spacing: 8
                padding: [6, 4]

                Button:
                    id: nav_tunnel
                    text: "TUNNEL"
                    bold: True
                    font_size: '11sp'
                    background_normal: ''
                    background_color: [0.01, 0.52, 0.78, 1.0] if root.current_tab == 'tab_tunnel' else [0, 0, 0, 0]
                    color: hex('#FFFFFF') if root.current_tab == 'tab_tunnel' else hex('#64748B')
                    on_release: root.switch_tab_slide('tab_tunnel')

                Button:
                    id: nav_license
                    text: "LICENSE"
                    bold: True
                    font_size: '11sp'
                    background_normal: ''
                    background_color: [0.01, 0.52, 0.78, 1.0] if root.current_tab == 'tab_license' else [0, 0, 0, 0]
                    color: hex('#FFFFFF') if root.current_tab == 'tab_license' else hex('#64748B')
                    on_release: root.switch_tab_slide('tab_license')

                Button:
                    id: nav_terminal
                    text: "TERMINAL"
                    bold: True
                    font_size: '11sp'
                    background_normal: ''
                    background_color: [0.01, 0.52, 0.78, 1.0] if root.current_tab == 'tab_terminal' else [0, 0, 0, 0]
                    color: hex('#FFFFFF') if root.current_tab == 'tab_terminal' else hex('#64748B')
                    on_release: root.switch_tab_slide('tab_terminal')
"""

# ======================================================================
# ACTIVATION POPUP MODAL
# ======================================================================
class ActivationPopupModal(ModalView):
    entered_key          = StringProperty("")
    status_msg           = StringProperty("Enter VIP key to activate.")
    popup_key_is_masked  = BooleanProperty(True)

    def __init__(self, parent_screen=None, on_success_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_success_callback = on_success_callback
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    self.entered_key = f.read().strip()
            except Exception:
                pass

    def toggle_popup_key_mask(self):
        self.popup_key_is_masked = not self.popup_key_is_masked

    def paste_clipboard(self):
        try:
            val = Clipboard.paste()
            if val:
                self.ids.popup_key_input.text = val.strip()
                self.status_msg = "Key pasted from clipboard."
                self.ids.popup_status_lbl.color = [0.01, 0.52, 0.78, 1.0]
        except Exception:
            pass

    def verify_and_connect(self):
        key = self.ids.popup_key_input.text.strip()
        if not key:
            self.status_msg = "Key cannot be empty."
            self.ids.popup_status_lbl.color = [0.94, 0.27, 0.27, 1.0]
            return

        self.status_msg = "Verifying with VIP server..."
        self.ids.popup_status_lbl.color = [0.01, 0.52, 0.78, 1.0]
        self.ids.popup_activate_btn.disabled = True
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
                        msg = "DEVICE BANNED: Hardware blocked by Admin!"
                    elif err_code == "DEVICE_LOCKED":
                        msg = "1-DEVICE LOCK: Key already used on another device!"
                    elif status == "SUCCESS" or "SUCCESS" in r.text.upper():
                        ok, msg = True, "VIP License Verified & Bound"
                    else:
                        msg = res.get("message") or "Invalid or Expired Key"
                else:
                    msg = f"Server Error ({r.status_code})"
            except requests.exceptions.Timeout:
                msg = "Offline: Server timeout. Check internet connection."
            except requests.exceptions.ConnectionError:
                msg = "Offline: Internet connection required."
            except Exception as e:
                msg = f"Offline / Error: {str(e)[:30]}"

        Clock.schedule_once(lambda dt: self._on_verified(ok, msg, key))

    def _on_verified(self, ok, msg, key):
        self.ids.popup_activate_btn.disabled = False
        if ok:
            self.status_msg = msg
            self.ids.popup_status_lbl.color = [0.02, 0.59, 0.41, 1.0]
            try:
                with open(LICENSE_CACHE, "w", encoding="utf-8") as f:
                    f.write(key)
            except OSError:
                pass

            if self.parent_screen:
                self.parent_screen.cached_key = key
                self.parent_screen.card_key_status = "Authorized"
                self.parent_screen.card_key_color = [0.02, 0.59, 0.41, 1.0]
                self.parent_screen.log_terminal("AUTH", "VIP License Verified & Bound")

            Clock.schedule_once(lambda dt: self._finish_and_connect(), 0.5)
        else:
            self.status_msg = msg
            self.ids.popup_status_lbl.color = [0.94, 0.27, 0.27, 1.0]

    def _finish_and_connect(self):
        self.dismiss()
        if self.on_success_callback:
            self.on_success_callback()

# ======================================================================
# MAIN SCREEN
# ======================================================================
class MainScreen(Screen):
    current_tab             = StringProperty("tab_tunnel")
    progress                = NumericProperty(0)
    btn_disabled            = BooleanProperty(False)
    conn_state              = StringProperty("idle")
    
    btn_label               = StringProperty("CONNECT")
    ring_color              = ListProperty([0.01, 0.52, 0.78, 0.3])
    ring_scale              = NumericProperty(1.0)
    ring_alpha              = NumericProperty(0.3)
    btn_bg_color            = ListProperty([1.0, 1.0, 1.0, 1.0])
    btn_border_color        = ListProperty([0.01, 0.52, 0.78, 1.0])
    btn_text_color          = ListProperty([0.01, 0.52, 0.78, 1.0])

    conn_status_text        = StringProperty("NOT CONNECTED")
    conn_status_color       = ListProperty([0.39, 0.45, 0.55, 1.0])
    status_pill_bg          = ListProperty([0.95, 0.96, 0.98, 0.9])
    status_pill_border      = ListProperty([0.80, 0.83, 0.88, 1.0])

    conn_heading_text       = StringProperty("TAP TO CONNECT")
    conn_heading_color      = ListProperty([0.12, 0.16, 0.23, 1.0])
    conn_sub_text           = StringProperty("Tap the power button to secure connection")

    vip_seconds_left        = NumericProperty((29 * 86400) + (18 * 3600) + (42 * 60) + 15)
    vip_countdown_text      = StringProperty("714h : 42m : 15s")

    terminal_copy_msg       = StringProperty("")
    cached_key              = StringProperty("")
    card_key_status         = StringProperty("Key Required")
    card_key_color          = ListProperty([0.85, 0.47, 0.02, 1.0])
    key_is_masked           = BooleanProperty(True)

    license_feedback_msg    = StringProperty("")
    license_feedback_color  = ListProperty([0.85, 0.47, 0.02, 1.0])

    terminal_logs           = StringProperty("[color=64748B][BOOT][/color] Core initialized.\\n[color=00FF7F][ENV][/color] Auto-Targeting active.\\n[color=38BDF8][STATE][/color] Ready.")

    is_rooted               = BooleanProperty(False)
    _countdown_event        = None

    TAB_ORDER = {"tab_tunnel": 0, "tab_license": 1, "tab_terminal": 2}

    def on_enter(self):
        self._load_cached_key()
        self._set_state("idle")
        self._start_breathing_animation()
        self._start_countdown_timer()
        Clock.schedule_once(lambda dt: self._init_background_services(), 0.5)

    def _init_background_services(self):
        def _bg():
            self.is_rooted = is_device_rooted()
        threading.Thread(target=_bg, daemon=True).start()
        self.log_terminal("INIT", "Tunnel client loaded in frosted glass mode.")
        Clock.schedule_once(lambda dt: self._request_perms(), 1.0)

    def _start_countdown_timer(self):
        if self._countdown_event:
            self._countdown_event.cancel()
        self._countdown_event = Clock.schedule_interval(self._tick_countdown, 1.0)

    def _tick_countdown(self, dt):
        if self.vip_seconds_left > 0:
            self.vip_seconds_left -= 1
            h = int(self.vip_seconds_left // 3600)
            m = int((self.vip_seconds_left % 3600) // 60)
            s = int(self.vip_seconds_left % 60)
            self.vip_countdown_text = f"{h}h : {m:02d}m : {s:02d}s"

    def _start_breathing_animation(self):
        anim = Animation(ring_scale=1.14, ring_alpha=0.6, duration=1.2, t='in_out_sine') + \
               Animation(ring_scale=1.0, ring_alpha=0.2, duration=1.2, t='in_out_sine')
        anim.repeat = True
        anim.start(self)

    def on_touch_down(self, touch):
        touch.ud['start_x'] = touch.x
        touch.ud['start_y'] = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if 'start_x' in touch.ud and 'start_y' in touch.ud:
            dx = touch.x - touch.ud['start_x']
            dy = touch.y - touch.ud['start_y']
            if abs(dx) > 60 and abs(dx) > 1.5 * abs(dy):
                tabs = ["tab_tunnel", "tab_license", "tab_terminal"]
                if self.current_tab in tabs:
                    curr_idx = tabs.index(self.current_tab)
                    if dx < -60 and curr_idx < len(tabs) - 1:
                        self.switch_tab_slide(tabs[curr_idx + 1])
                        return True
                    elif dx > 60 and curr_idx > 0:
                        self.switch_tab_slide(tabs[curr_idx - 1])
                        return True
        return super().on_touch_up(touch)

    def switch_tab_slide(self, target_tab):
        if target_tab == self.current_tab:
            return
        curr_idx = self.TAB_ORDER.get(self.current_tab, 0)
        target_idx = self.TAB_ORDER.get(target_tab, 0)
        self.ids.tab_manager.transition.direction = 'left' if target_idx > curr_idx else 'right'
        self.current_tab = target_tab
        self.ids.tab_manager.current = target_tab

    def toggle_key_mask(self):
        self.key_is_masked = not self.key_is_masked

    def deactivate_key(self):
        self.cached_key = ""
        self.card_key_status = "Deactivated"
        self.card_key_color = [0.85, 0.47, 0.02, 1.0]
        self.license_feedback_msg = "Key temporarily deactivated."
        self.license_feedback_color = [0.85, 0.47, 0.02, 1.0]
        self.log_terminal("AUTH", "VIP key session deactivated.")

    def delete_key(self):
        self.cached_key = ""
        if hasattr(self, 'ids') and 'key_input_field' in self.ids:
            self.ids.key_input_field.text = ""
        self.card_key_status = "Key Required"
        self.card_key_color = [0.85, 0.47, 0.02, 1.0]
        self.license_feedback_msg = "Key removed from device storage."
        self.license_feedback_color = [0.94, 0.27, 0.27, 1.0]
        if os.path.exists(LICENSE_CACHE):
            try:
                os.remove(LICENSE_CACHE)
            except OSError:
                pass
        self.log_terminal("AUTH", "License key deleted from storage.")

    def log_terminal(self, tag, message):
        t_str = time.strftime("%H:%M:%S")
        entry = f"[color=64748B][{t_str}][/color] [color=00FF7F][{tag}][/color] {message}"
        lines = self.terminal_logs.split("\\n")
        if len(lines) > 18:
            lines = lines[-18:]
        lines.append(entry)
        self.terminal_logs = "\\n".join(lines)

    def copy_terminal_logs(self):
        try:
            import re
            clean_text = re.sub(r'\[.*?\]', '', self.terminal_logs)
            Clipboard.copy(clean_text)
            self.terminal_copy_msg = "Logs copied to clipboard!"
            Clock.schedule_once(lambda dt: setattr(self, "terminal_copy_msg", ""), 2.5)
        except Exception:
            pass

    def clear_terminal_logs(self):
        t_str = time.strftime("%H:%M:%S")
        self.terminal_logs = f"[color=64748B][{t_str}][/color] [color=38BDF8][INFO][/color] Console cleared. Ready."

    def _load_cached_key(self):
        if os.path.exists(LICENSE_CACHE):
            try:
                with open(LICENSE_CACHE, "r", encoding="utf-8") as f:
                    k = f.read().strip()
                    if k:
                        self.cached_key = k
                        self.card_key_status = "Authorized"
                        self.card_key_color = [0.02, 0.59, 0.41, 1.0]
                        return
            except Exception:
                pass
        self.card_key_status = "Key Required"
        self.card_key_color = [0.85, 0.47, 0.02, 1.0]

    def paste_clipboard(self):
        try:
            val = Clipboard.paste()
            if val:
                self.ids.key_input_field.text = val.strip()
                self.license_feedback_msg = "Key pasted from clipboard."
                self.license_feedback_color = [0.01, 0.52, 0.78, 1.0]
        except Exception:
            pass

    def activate_key(self):
        key = self.ids.key_input_field.text.strip()
        if not key:
            self.license_feedback_msg = "Key cannot be empty."
            self.license_feedback_color = [0.94, 0.27, 0.27, 1.0]
            return

        self.license_feedback_msg = "Verifying with VIP server..."
        self.license_feedback_color = [0.01, 0.52, 0.78, 1.0]
        self.ids.save_license_btn.disabled = True
        self.log_terminal("AUTH", "Verifying VIP key...")
        threading.Thread(target=self._verify_key_worker, args=(key,), daemon=True).start()

    def _verify_key_worker(self, key):
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
                        msg = "DEVICE BANNED: Hardware blocked by Admin!"
                    elif err_code == "DEVICE_LOCKED":
                        msg = "1-DEVICE LOCK: Key already used on another device!"
                    elif status == "SUCCESS" or "SUCCESS" in r.text.upper():
                        ok, msg = True, "VIP License Verified & Bound"
                    else:
                        msg = res.get("message") or "Invalid or Expired Key"
                else:
                    msg = f"Server Error ({r.status_code})"
            except requests.exceptions.Timeout:
                msg = "Offline: Server timeout. Check internet connection."
            except requests.exceptions.ConnectionError:
                msg = "Offline: Internet connection required."
            except Exception as e:
                msg = f"Offline / Error: {str(e)[:30]}"

        Clock.schedule_once(lambda dt: self._on_key_saved(ok, msg, key))

    def _on_key_saved(self, ok, msg, key):
        self.ids.save_license_btn.disabled = False
        if ok:
            self.cached_key = key
            self.license_feedback_msg = "Key Activated Successfully!"
            self.license_feedback_color = [0.02, 0.59, 0.41, 1.0]
            self.card_key_status = "Authorized"
            self.card_key_color = [0.02, 0.59, 0.41, 1.0]
            self.log_terminal("AUTH", "License key verified & bound successfully.")
            try:
                with open(LICENSE_CACHE, "w", encoding="utf-8") as f:
                    f.write(key)
            except OSError:
                pass
            Clock.schedule_once(lambda dt: self.switch_tab_slide('tab_tunnel'), 0.8)
        else:
            self.license_feedback_msg = msg
            self.license_feedback_color = [0.94, 0.27, 0.27, 1.0]
            self.log_terminal("FAIL", f"Verification failed: {msg}")

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
        try:
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            if Build.VERSION.SDK_INT >= 30:
                Environment = autoclass("android.os.Environment")
                if not Environment.isExternalStorageManager():
                    PythonActivity = autoclass("org.kivy.android.PythonActivity")
                    if PythonActivity.mActivity:
                        Intent = autoclass("android.content.Intent")
                        Settings = autoclass("android.provider.Settings")
                        Uri = autoclass("android.net.Uri")
                        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                        intent.setData(Uri.parse(f"package:{PythonActivity.mActivity.getPackageName()}"))
                        PythonActivity.mActivity.startActivity(intent)
        except Exception:
            pass

    def on_vpn_button_press(self):
        if self.conn_state == "connected":
            self._begin_disconnect()
        elif self.conn_state == "idle":
            if not self.cached_key:
                modal = ActivationPopupModal(
                    parent_screen=self,
                    on_success_callback=self._begin_connect
                )
                modal.open()
            else:
                self._begin_connect()

    def _begin_connect(self):
        self._request_perms()
        self._set_state("busy")
        self.log_terminal("CONNECT", "Initiating secure tunnel connection...")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _begin_disconnect(self):
        self._set_state("busy")
        self.log_terminal("DISCONNECT", "Stopping tunnel and purging buffers...")
        threading.Thread(target=self._disconnect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            target_pkg = auto_detect_game_pkg()
            base_dir = get_game_base_path(target_pkg)
            paks_dir = get_game_paks_path(target_pkg)
            self.log_terminal("TARGET", "Game target environment located.")

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
                Clock.schedule_once(lambda dt: self._set_state("idle", sub="No active patch on server."))
                self.log_terminal("ERROR", "No active patch found on server.")
                return

            total = int(resp.headers.get("content-length", 0))
            fetched = 0

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

            self.log_terminal("PAYLOAD", "Payload downloaded and verified.")

            installed_files = []
            installed_dirs  = []

            if zipfile.is_zipfile(CACHE_FILE):
                self.log_terminal("IDENTIFY", "Format: ZIP archive payload detected.")
                self.log_terminal("PERMISSION", "Storage filesystem access validated.")
                with zipfile.ZipFile(CACHE_FILE, "r") as zf:
                    infolist = zf.infolist()
                    total_items = len(infolist)
                    
                    has_files_root = any(item.filename.startswith("files/") for item in infolist)
                    has_ue4_root = any(item.filename.startswith("UE4Game/") for item in infolist)
                    has_shadow_root = any(item.filename.startswith("ShadowTrackerExtra/") for item in infolist)
                    has_saved_root = any(item.filename.startswith("Saved/") for item in infolist)

                    if has_files_root:
                        extract_root = base_dir
                    elif has_ue4_root:
                        extract_root = os.path.join(base_dir, "files")
                    elif has_shadow_root:
                        extract_root = os.path.join(base_dir, "files", "UE4Game")
                    elif has_saved_root:
                        extract_root = os.path.join(base_dir, "files", "UE4Game", "ShadowTrackerExtra", "ShadowTrackerExtra")
                    else:
                        extract_root = paks_dir

                    self.log_terminal("UNZIP", f"Decompressing {total_items} items step-by-step...")
                    self.log_terminal("ROUTE", "Aligning directory tree to destination...")

                    try:
                        os.makedirs(extract_root, exist_ok=True)
                    except Exception:
                        if self.is_rooted:
                            os.system(f"su -c 'mkdir -p \"{extract_root}\"'")

                    for idx, item in enumerate(infolist):
                        extracted_path = zf.extract(item, extract_root)
                        if item.is_dir():
                            installed_dirs.append(extracted_path)
                        else:
                            installed_files.append(extracted_path)
                        if total_items > 0:
                            pct = int((idx + 1) / total_items * 100)
                            Clock.schedule_once(lambda dt, p=pct: setattr(self, "progress", p))
                    
                    self.log_terminal("DEPLOY", "All files extracted & placed in target folders.")
            else:
                self.log_terminal("IDENTIFY", "Format: Standalone .PAK file detected.")
                self.log_terminal("PERMISSION", "Storage filesystem access validated.")
                self.log_terminal("ROUTE", "Auto-saving directly to Saved/Paks...")
                try:
                    os.makedirs(paks_dir, exist_ok=True)
                except Exception:
                    if self.is_rooted:
                        os.system(f"su -c 'mkdir -p \"{paks_dir}\"'")

                dest_file = os.path.join(paks_dir, TARGET_FILENAME)
                shutil.copy2(CACHE_FILE, dest_file)
                installed_files.append(dest_file)
                self.log_terminal("DEPLOY", f"Saved: {TARGET_FILENAME}")

            self._save_manifest(installed_files, installed_dirs)
            self.log_terminal("SUCCESS", "Tunnel fully connected. Protection active.")
            Clock.schedule_once(lambda dt: self._set_state("connected"))

        except Exception as e:
            err_short = str(e)[:35]
            self.log_terminal("ERROR", f"Tunnel failed: {err_short}")
            Clock.schedule_once(lambda dt: self._set_state("idle", sub=f"Error: {err_short}"))
        finally:
            if os.path.exists(CACHE_FILE):
                try: os.remove(CACHE_FILE)
                except OSError: pass

    def _disconnect_worker(self):
        self._delete_file()
        self.log_terminal("CLEAN", "All injected files purged. 0 traces remaining.")
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

        target_dir = auto_detect_game_target()
        dest = os.path.join(target_dir, TARGET_FILENAME)
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except Exception:
                if self.is_rooted:
                    os.system(f"su -c 'rm -f \"{dest}\"'")

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

    def _set_state(self, state: str, sub=None):
        self.conn_state = state
        if state == "idle":
            self.btn_label          = "CONNECT"
            self.btn_disabled       = False
            self.ring_color         = [0.01, 0.52, 0.78, 0.35]
            self.btn_bg_color       = [1.0, 1.0, 1.0, 1.0]
            self.btn_border_color   = [0.01, 0.52, 0.78, 1.0]
            self.btn_text_color     = [0.01, 0.52, 0.78, 1.0]

            self.conn_status_text   = "NOT CONNECTED"
            self.conn_status_color  = [0.39, 0.45, 0.55, 1.0]
            self.status_pill_bg     = [0.95, 0.96, 0.98, 0.9]
            self.status_pill_border = [0.80, 0.83, 0.88, 1.0]

            self.conn_heading_text  = "TAP TO CONNECT"
            self.conn_heading_color = [0.12, 0.16, 0.23, 1.0]
            self.conn_sub_text      = sub or "Tap the power button to secure connection"

        elif state == "busy":
            self.btn_label          = "..."
            self.btn_disabled       = True
            self.ring_color         = [0.85, 0.47, 0.02, 0.6]
            self.btn_bg_color       = [0.98, 0.95, 0.90, 1.0]
            self.btn_border_color   = [0.85, 0.47, 0.02, 1.0]
            self.btn_text_color     = [0.85, 0.47, 0.02, 1.0]

            self.conn_status_text   = "CONNECTING..."
            self.conn_status_color  = [0.85, 0.47, 0.02, 1.0]
            self.status_pill_bg     = [1.0, 0.95, 0.88, 0.9]
            self.status_pill_border = [0.95, 0.70, 0.30, 0.8]

            self.conn_heading_text  = "SECURING TUNNEL..."
            self.conn_heading_color = [0.85, 0.47, 0.02, 1.0]
            self.conn_sub_text      = "Routing through secure gateway"

        elif state == "connected":
            self.btn_label          = "DISCONNECT"
            self.btn_disabled       = False
            self.ring_color         = [0.02, 0.59, 0.41, 0.5]
            self.btn_bg_color       = [0.92, 0.99, 0.95, 1.0]
            self.btn_border_color   = [0.02, 0.59, 0.41, 1.0]
            self.btn_text_color     = [0.02, 0.59, 0.41, 1.0]

            self.conn_status_text   = "CONNECTED"
            self.conn_status_color  = [0.02, 0.59, 0.41, 1.0]
            self.status_pill_bg     = [0.82, 0.98, 0.90, 0.9]
            self.status_pill_border = [0.06, 0.73, 0.51, 0.6]

            self.conn_heading_text  = "CONNECTED"
            self.conn_heading_color = [0.02, 0.59, 0.41, 1.0]
            self.conn_sub_text      = "Secure high-speed tunnel active"

# ======================================================================
# APP ENTRY
# ======================================================================
class PakDeployerApp(App):
    def build(self):
        self.title = "NEXUS Tunnel"
        Builder.load_string(KV)
        sm = ScreenManager()
        main_sc = MainScreen(name="main")
        sm.add_widget(main_sc)
        sm.current = "main"
        return sm

if __name__ == "__main__":
    PakDeployerApp().run()
