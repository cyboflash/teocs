import re
import sys
import os

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : Parser
# Description: Parses the .asm file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Parser(object):
    A_COMMAND = 0 # A_COMMAND for @Xxx where Xxx s either a symbol or a decimal number
    C_COMMAND = 1 # for dest=comp;jmp
    L_COMMAND = 2 # (pseudocommand) for (Xxx) where Xxx s a symbol
    U_COMMAND = 3 # Unknown command
    
    COMP = '0|1|-1|D|A|!D|!A|-D|-A|D\+1|A\+1|D-1|A-1|D\+A|D-A|A-D|D&A|D\|A|M|!M|-M|M\+1|M-1|D\+M|D-M|M-D|D&M|D\|M'
    JUMP = 'JGT|JEQ|JGE|JLT|JNE|JLE|JMP'
    DEST = 'M|D|MD|A|AM|AD|AMD'
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __init__
    # Description: Constructor. Tries to open the fileName and gets ready to
    #              parse it. If it can't then it raises an exception
    # Parameters : fileName(string) - path to the file to be parsed
    # Return     : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, fileName):
        self._line = ''
        self._f = None
        
        try:
            self._f = open(fileName)
        except Exception as err:
            print(err)
            sys.exit(1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : advance
    # Description: Reads the next command from the input and makes the current
    #              command. Returns True if a line from the file was read, False
    #              if the end of file is reached. Upon reaching the end of file
    #              this function will close it.
    # Parameters : None
    # Returns    : True if end of file was not reached, i.e. this it was able to
    #              advance, False - otherwise
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def advance(self):
        self._line = self._f.readline()
        while self._line:
            # remove comments
            self._line = re.sub('\/\/.*', '', self._line)
            #remove white space
            while re.match('\s+', self._line, re.S):
                self._line = re.sub('\s+', '', self._line)

            if self._line:
                return True
            
            self._line = self._f.readline()
            
        self._f.close()    
        return False
                
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : commandType
    # Description: Returns the type of the current command
    #              A_COMMAND for @Xxx where Xxx is either a symbol or a number
    #              C_COMMAND for dest=comp;jump
    #              L_COMMAND (actually, pseudo-command for (Xxx) where Xxx is a
    #              symbol
    # Parameters : None
    # Return     : A_COMMAND, C_COMMAND, L_COMMAND
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def commandType(self):
        if re.match(r'^@.+$', self._line):
            return type(self).A_COMMAND
        elif re.match('^(?:(?:'+type(self).DEST+')=(?:'+type(self).COMP+'))$|^(?:(?:'+type(self).COMP+');(?:'+type(self).JUMP+'))$', self._line):
            return type(self).C_COMMAND
        elif re.match(r'^\(.+\)$', self._line):
            return type(self).L_COMMAND
        else:
            return type(self).U_COMMAND
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : symbol
    # Description: Returns the symbol or decimal Xxx of the current command
    #              @Xxx or (Xxx). Should be called only when commandType() is
    #              A_COMMAND or L_COMMAND
    # Parameters : None
    # Return     : symbol(string)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def symbol(self):
        m1 = re.match(r'^@(.+)$', self._line)
        m2 = re.match(r'^\((.+)\)$', self._line)
        if m1:
            return m1.group(1)
        elif m2:
            return m2.group(1)
        return None
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : dest
    # Description: Returns the dest mnemonic in the current C-command
    #              (8 possibilities). Should be called only when commandType() is
    #              C_COMMAND
    # Parameters : None
    # Return     : destination(string)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def dest(self):
        m = re.match('^('+type(self).DEST+')=', self._line)
        if m:
            return m.group(1)
        return None
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : comp
    # Description: Returns the comp mnemonic in the current C-command
    #              (28 possibilities). Should be called only when commandType()
    #              is C_COMMAND
    # Parameters : None
    # Return     : compute(string)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def comp(self):
        m1 = re.match('^('+type(self).COMP+');', self._line)
        m2 = re.search('=('+type(self).COMP+')$', self._line)
        if m1:
            return m1.group(1)
        elif m2:
            return m2.group(1)
        
        return None
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       :jump
    # Description: Returns the jump mnemonic in the current C-command
    #              (8 possibilities). Should be called only when commandType()
    #              is C_COMMAND
    # Parameters : None
    # Return     : jump(string)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def jump(self):
        m = re.search('('+type(self).JUMP+')$', self._line)
        if m:
            return m.group(1)
        return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name: Code
# Description: Generates binary code
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Code(object):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : dest
    # Description: Returns the binary code of the dest mnemonic
    # Parameters : string - dest mnemonic
    # Return     : binary code of the dest mnemonic
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def dest(self, string):
        if string is None:
            return '000'
        elif 'M' == string:
            return '001'
        elif 'D' == string:
            return '010'
        elif 'MD' == string:
            return '011'
        elif 'A' == string:
            return '100'
        elif 'AM' == string:
            return '101'
        elif 'AD' == string:
            return '110'
        elif 'AMD' == string:
            return '111'
        return None
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : comp
    # Description: Returns the binary code of the comp mnemonic
    # Parameters : string - comp mnemonic
    # Return     : binary code of the comp mnemonic
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    def comp(self, string):
        if '0' == string:
            return '0101010'
        elif '1' == string:
            return '0111111'
        elif '-1' == string:
            return '0111010'
        elif 'D' == string:
            return '0001100'
        elif 'A' == string:
            return '0110000'
        elif '!D' == string:
            return '0001101'
        elif '!A' == string:
            return '0110001'
        elif '-D' == string:
            return '0001111'
        elif '-A' == string:
            return '0110011'
        elif 'D+1' == string:
            return '0011111'
        elif 'A+1' == string:
            return '0110111'
        elif 'D-1' == string:
            return '0001110'
        elif 'A-1' == string:
            return '0110010'
        elif 'D+A' == string:
            return '0000010'
        elif 'D-A' == string:
            return '0010011'
        elif 'A-D' == string:
            return '0000111'
        elif 'D&A' == string:
            return '0000000'
        elif 'D|A' == string:
            return '0010101'
        elif 'M' == string:
            return '1110000'
        elif '!M' == string:
            return '1110001'
        elif '-M' == string:
            return '1110011'
        elif 'M+1' == string:
            return '1110111'
        elif 'M-1' == string:
            return '1110010'
        elif 'D+M' == string:
            return '1000010'
        elif 'D-M' == string:
            return '1010011'
        elif 'M-D' == string:
            return '1000111'
        elif 'D&M' == string:
            return '1000000'
        elif 'D|M' == string:
            return '1010101'
        return None
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : jump
    # Description: Returns the binary code of the jump mnemonic
    # Parameters : string - jump mnemonic
    # Return     : binary code of the jump mnemonic
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    def jump(self, string):
        if string is None:
            return '000'
        elif 'JGT' == string:
            return '001'
        elif 'JEQ' == string:
            return '010'
        elif 'JGE' == string:
            return '011'
        elif 'JLT' == string:
            return '100'
        elif 'JNE' == string:
            return '101'
        elif 'JLE' == string:
            return '110'
        elif 'JMP' == string:
            return '111'
        return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : SymbolTable
# Description: Represents a symbol table for the assembler
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SymbolTable(object):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __init__
    # Description: Constructor. Creates a new symbol table and initializes it
    #              with all the predefined symbols and their pre-allocated RAM
    #              addresses
    # Parameters : None
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self):
        self._table = {
            'SP' : 0,
            'LCL' : 1,
            'ARG' : 2,
            'THIS' : 3,
            'THAT' : 4,
            'SCREEN' : 16384,
            'KBD' : 24576
        }
        for i in range(16):
            self._table['R'+str(i)] = i

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : addEntry
    # Description: Adds the pair (symbol, address) to the table
    # Parameters : symbol(string), address(string)
    # Returns    : Nothing 
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def addEntry(self, symbol, address):
        self._table[symbol] = address
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : contains
    # Description: Does the symbol table contain the given symbol?
    # Parameters : symbol(string)
    # Returns    : True if the symbol is in the table, False if it is not 
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def contains(self, symbol):
        return symbol in self._table
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : getAddress
    # Description: Returns the address associated with the symbol
    # Parameters : symbol(string)
    # Returns    : address associated with the symbol
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getAddress(self, symbol):
        return self._table[symbol]
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : dec2bin
# Description: converts decimal to binary with 15 bits. binary equivalend of a
#              decimal should not be more than 15 bits long. if it is then 15
#              lowest bits are returned
# Parameters : nbr(decimal)
# Return     : binary(string)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def dec2bin(nbr):
    m = re.search('^0b[01]*?([01]{,15}$)', bin(int(nbr)))
    if m:
        preprend = 15 - len(m.group(1))
        return preprend*'0' + m.group(1)
    return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# main code
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    usage = sys.argv[0] + ' filename'
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)
        
    asmfilename = sys.argv[1]

    ### first pass ###
    romAddr = 0
    parser = Parser(asmfilename)
    symbolTable = SymbolTable()
    while(parser.advance()):
        if parser.L_COMMAND == parser.commandType():
            symbolTable.addEntry(parser.symbol(), romAddr)
            continue
        
        romAddr = romAddr + 1

    ### second pass ###
    ramAddr = 16
    hackfile = None

    # make sure the input file exists and extract its name
    if os.path.isfile(asmfilename):
        m = re.match(r'(.*?)\..*', asmfilename)
        hackfile = open(m.group(1)+'.hack', 'w')
    else:
        print('Error: File ' + asmfilename + ' cannot be opened.')
        sys.exit(1)
    
    parser = Parser(asmfilename)
    code = Code()
    
    # march through the lines in the .asm file
    while(parser.advance()):
        hackstr = ''
        # process the C_COMMAND ...
        if parser.C_COMMAND == parser.commandType():
            # and extract destinaton, compute and jump fields
            comp = parser.comp()
            dest = parser.dest()
            jump = parser.jump()

            # print('dest =', dest, 'comp =', comp, 'jump =', jump)
            # create a binary string in hack language
            hackstr = '111'+code.comp(comp)+code.dest(dest)+code.jump(jump)

        # process the A_COMMAND 
        elif parser.A_COMMAND == parser.commandType():
            symbol = parser.symbol()

            # check if symbol is not an address, i.e. consists only of digits
            # if it is not an address then it means that it is either a
            # reference to a label or a new variable
            m = re.match(r'\D+', symbol)
            if m:
                # check if it is a reference to a label, i.e. check if the
                # symbol is in the symbol table
                if symbolTable.contains(symbol):
                    # if it is then extract the value of the symbol
                    symbol = symbolTable.getAddress(symbol)
                # if symbol table doesn't contain this symbol then it is a
                # a new RAM variable and we need to add to the symbol table.
                else:
                    symbolTable.addEntry(symbol, ramAddr)
                    symbol = ramAddr
                    ramAddr = ramAddr + 1
                
            # create a binary string in hack language
            hackstr = '0' + dec2bin(symbol)

        # write the binary string into the hack file if it is not empty.
        # empty strings occur of the type of command encountered is an
        # L_COMMAND, which is not processed by the second pass but processed
        # in the first pass
        if hackstr:
            hackfile.write(hackstr + '\n')

    hackfile.close()
    
    for key in symbolTable._table.keys():
        print('{} : {}\r\n'.format(key, symbolTable._table[key]))
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Let's go ...
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if '__main__' == __name__:
    main()
