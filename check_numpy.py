import sys
print("Python version:", sys.version)
try:
    import numpy
    print("numpy version:", numpy.__version__)
except:
    print("numpy NOT available")
