import platform
from sys import stdout

if platform.system()=="Linux":
    pass
else:
    from colorama import init
    init()

# Do you like the elegance of Chinese characters?
def PrintRed(*kw,**kargs):
    print("\033[0;31m",*kw,"\033[0m",**kargs)
def PrintGreen(*kw,**kargs):
    print("\033[0;32m",*kw,"\033[0m",**kargs)
def PrintYellow(*kw,**kargs):
    print("\033[0;33m",*kw,"\033[0m",**kargs)
def PrintBlue(*kw,**kargs):
    print("\033[0;34m",*kw,"\033[0m",**kargs)
def PrintPurple(*kw,**kargs):
    print("\033[0;35m",*kw,"\033[0m",**kargs)
def PrintIndigo(*kw,**kargs):
    print("\033[0;36m",*kw,"\033[0m",**kargs)

def PrintBrightRed(*kw,**kargs):
    print("\033[1;31m",*kw,"\033[0m",**kargs)
def PrintBrightGreen(*kw,**kargs):
    print("\033[1;32m",*kw,"\033[0m",**kargs)
def PrintBrightYellow(*kw,**kargs):
    print("\033[1;33m",*kw,"\033[0m",**kargs)
def PrintBrightBlue(*kw,**kargs):
    print("\033[1;34m",*kw,"\033[0m",**kargs)
def PrintBrightPurple(*kw,**kargs):
    print("\033[1;35m",*kw,"\033[0m",**kargs)
def PrintBrightIndigo(*kw,**kargs):
    print("\033[1;36m",*kw,"\033[0m",**kargs)

# Do you like the elegance of Chinese characters?
def sPrintRed(*kw):
    return "\033[0;31m"+' '.join(kw)+"\033[0m"
def sPrintGreen(*kw):
    return "\033[0;32m"+' '.join(kw)+"\033[0m"
def sPrintYellow(*kw):
    return "\033[0;33m"+' '.join(kw)+"\033[0m"
def sPrintBlue(*kw):
    return "\033[0;34m"+' '.join(kw)+"\033[0m"
def sPrintPurple(*kw):
    return "\033[0;35m"+' '.join(kw)+"\033[0m"
def sPrintIndigo(*kw):
    return "\033[0;36m"+' '.join(kw)+"\033[0m"
def sPrintBrightRed(*kw):
    return "\033[1;31m"+' '.join(kw)+"\033[0m"
def sPrintBrightGreen(*kw):
    return "\033[1;32m"+' '.join(kw)+"\033[0m"
def sPrintBrightYellow(*kw):
    return "\033[1;33m"+' '.join(kw)+"\033[0m"
def sPrintBrightBlue(*kw):
    return "\033[1;34m"+' '.join(kw)+"\033[0m"
def sPrintBrightPurple(*kw):
    return "\033[1;35m"+' '.join(kw)+"\033[0m"
def SprintIndigo(*kw):
    return "\033[1;36m"+' '.join(kw)+"\033[0m"
