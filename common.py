#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def clear_screen():
    """Efface l'écran de la console de manière multiplateforme"""
    # Pour Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # Pour Mac et Linux (os.name est 'posix')
    else:
        _ = os.system('clear')
