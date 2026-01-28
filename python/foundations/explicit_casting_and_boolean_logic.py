"""
Explicit Casting & Boolean Logic — Python Foundations for Data Engineering

Why this file exists
--------------------
In data engineering, raw values usually arrive as STRINGS
(from CSV, JSON, configs, env vars).

This file demonstrates:
- why Python does NOT auto-convert types
- how explicit casting changes behavior
- how comparisons produce True/False
- how boolean logic combines conditions predictably

No functions. No classes.
Only core execution rules.
"""

# 1) Same value, different types → False
print("10" == 10)          # False
print(int("10") == 10)     # True


# 2) String comparison is lexicographic (not numeric)
print("5" > "12")          # True  ('5' > '1')
print(int("5") > int("12"))  # False (numeric comparison)


# 3) Arithmetic happens in the CURRENT type until you cast
x = "4"
print(x * 2 + "1")         # "441"
print(int(x * 2) + 1)     # 45


# 4) Comparisons create booleans
a = int("3") * 2 == 6      # True
b = int("5") > 10          # False

print(a)
print(b)


# 5) Boolean logic combines comparisons
print(a and b)             # False
print(a or b)              # True
print(not b)               # True


# 6) Realistic validation-style expression (no if yet)
latency_ms = int("650")
error_rate = float("0.03")

print(latency_ms >= 500 and error_rate >= 0.02)  # True
