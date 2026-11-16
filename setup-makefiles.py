#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import os
import sys
from pathlib import Path

extractor = Path(__file__).resolve().with_name('extract-files.py')
os.execv(str(extractor), [str(extractor), '--regenerate_makefiles', *sys.argv[1:]])
