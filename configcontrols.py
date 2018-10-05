from __future__ import unicode_literals
import os

class ConfigControls( object ):
    def __init__(self):
        # self.path = '/home/pi/WakePi/'
        self.path = os.path.dirname(os.path.abspath(__file__))+'\\'
        
    def get_section(self,section,return_other_text=False):
        '''Returns the section from the config file'''
        section_text = []
        other_text = [[],[]]
        index = 0
        flag_section = False
        full_text = open(self.path+'config.txt','r')
        for line in full_text:
            if flag_section:
                if '[' in line:
                    flag_section = False
                    other_text[index].append(line)
                elif line != '\n':
                    section_text.append(line.strip())
                else:
                    other_text[index].append(line)
            elif '['+section.strip()+']' in line:
                flag_section = True
                other_text[index].append(line)
                index += 1
            else:
                other_text[index].append(line)
        if return_other_text:
            return [section_text,other_text]
        else:
            return section_text

    def set_section(self,section_name,section_list):
        try:
            [section_text,other_text] = self.get_section(section_name,True)
            section_list.append('')
            file = open(self.path+'config.txt','w')
            file.write(''.join(other_text[0])
                       +'\n'.join(section_list)
                       +''.join(other_text[1]))
            return True
        except Exception as error:
            print(error)
            return False
