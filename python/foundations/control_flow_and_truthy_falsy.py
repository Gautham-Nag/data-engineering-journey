"""
Control Flow & Truthy/Falsy — Python Execution Foundations

Why this file exists
--------------------
In real Python programs (and data pipelines), conditions are often written as:
    if x:
    if records:
    if value:

This file demonstrates:
- how `if / elif / else` route execution
- how truthy/falsy values control those routes
- why EMPTY vs NON-EMPTY is the real decision
- how mixed string/numeric conditions behave

No functions. No classes.
Only execution behavior.
"""

# ------------------------------------------------------------
# 1) if / else controls ONLY its indented block
# ------------------------------------------------------------

if "5" > "12":           # string comparison → True
    print("A")

print("B")               # always runs


# ------------------------------------------------------------
# 2) if / elif / else is a ladder (first True wins)
# ------------------------------------------------------------

x = "12"

if int(x) < 5:
    print("Low")
elif x < "2":            # string comparison → True ('1' < '2')
    print("Medium")
else:
    print("High")

print("Done")


# ------------------------------------------------------------
# 3) Truthy vs Falsy — EMPTY vs NON-EMPTY
# ------------------------------------------------------------

value = ""

if value:
    print("Has value")
else:
    print("Empty value")


# ------------------------------------------------------------
# 4) Non-empty strings are Truthy (even if they look false)
# ------------------------------------------------------------

value = "0"

if value:
    print("Truthy string")
else:
    print("Falsy string")


# ------------------------------------------------------------
# 5) Empty vs non-empty containers
# ------------------------------------------------------------

records = []

if records:
    print("Process records")
else:
    print("No records to process")


records = [0]

if records:
    print("Process records")
else:
    print("No records to process")
