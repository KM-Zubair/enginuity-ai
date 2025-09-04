import os, sys

print("=== Current Working Directory ===")
print(os.getcwd())

print("\n=== sys.path (where Python looks for imports) ===")
for p in sys.path:
    print(p)

print("\n=== Files/Folders in project root ===")
for f in os.listdir("."):
    print(" -", f)

print("\n=== Files/Folders in ui/ ===")
if os.path.exists("ui"):
    for f in os.listdir("ui"):
        print(" -", f)
else:
    print("ui folder not found")
