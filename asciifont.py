from __future__ import unicode_literals

class AsciiFont( object ):
    def __init__(self):
        self.number = [[],[],[],[],[],[],[],[],[],[]]
        self.number[0]=['  .oooo.  ',
                        ' d8P""Y8b ',
                        '888    888',
                        '888    888',
                        '888    888',
                        '"88b  d88"',
                        ' "Y8bd8P" ']
        self.number[1]=['     .o   ',
                        '   o888   ',
                        '  oH888   ',
                        '    888   ',
                        '    888   ',
                        '    888   ',
                        '  od888bo ']
        self.number[2]=['  .oooo.  ',
                        '.dP""Y88b ',
                        '      ]8P"',
                        '    .d8P" ',
                        '  .dP"    ',
                        '.oP     .o',
                        '8888888888']
        self.number[3]=['  .oooo.  ', 
                        '.dP""Y88b ',
                        '      ]8P"',
                        '    <88b. ',
                        '     "88b.',
                        'o.   .88P ',
                        '"8bd88P"  ']
        self.number[4]=['      .o  ', 
                        '    .d88  ', 
                        '  .d"888  ',
                        '.d"  888  ', 
                        '88ooo888oo', 
                        '     888  ', 
                        '    o888o ']
        self.number[5]=['  oooooooo', 
                        ' dP"""""""', 
                        'd88888b.  ', 
                        '    "Y88b ', 
                        '      ]88 ', 
                        'o.   .88P ', 
                        '"8bd88P"  ']
        self.number[6]=['    .ooo  ', 
                        '  .88"    ', 
                        ' d88"     ', 
                        'd888P"Ybo.', 
                        'Y88[   ]88', 
                        '"Y88   88P', 
                        ' "88bod8" ']
        self.number[7]=[' ooooooooo', 
                        'd"""""""8"',
                        '      .8" ',
                        '     .8"  ',
                        '    .8"   ',
                        '   .8"    ',
                        '  .8"     ']
        self.number[8]=[' .ooooo.  ', 
                        'd88"   "8.', 
                        'Y88..  .8"', 
                        ' "88888b. ', 
                        '.8"  ""88b', 
                        '"8.   .88P', 
                        ' "boood8" ']
        self.number[9]=[' .ooooo.  ', 
                        '888" "Y88.', 
                        '888    888', 
                        ' "Vbood888', 
                        '      888"', 
                        '    .88P" ', 
                        '  .oP"    ']
        
    def __call__(self,num):
        return self.number[num]
        

