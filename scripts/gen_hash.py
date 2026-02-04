#!/usr/bin/env python3
import bcrypt

password = "Test2025!Secure"
h = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
print(h)
