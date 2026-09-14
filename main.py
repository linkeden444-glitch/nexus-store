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
