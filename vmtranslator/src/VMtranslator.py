#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : VMtranslator
# Description: Parses .vm files and generates .asm files for the Hack platform
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import sys
import re
import os

C_ARITHMETIC = 0
C_PUSH       = 1
C_POP        = 2
C_LABEL      = 3
C_GOTO       = 4
C_IF         = 5
C_FUNCTION   = 6
C_RETURN     = 7
C_CALL       = 8
C_UNKNOWN    = 9

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : Parser
# Description: Handles the parsing of a signle .vm file, and encapsulates access
#              to the input code. It reads VM commands, parses them, and
#              provides convenient access to their components. In addition it
#              removes all white spaces and comments.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Parser(object):
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __init__
    # Description: Constructor. Opens the input file and gets ready to parse it.
    # Parameters : string : fileName - path the the file to be parsed
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, fileName):
        try:
            self._f = open(fileName)
        except Exception as err:
            print(err)
            sys.exit(1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : advance
    # Description: Reads the next command from the input and makes it the
    #              current command. Upon reaching the end of the file this
    #              method will close it.
    # Parameters : None
    # Returns    : True if end of file was not reached, i.e. the method was able
    #              to advance, False - otherwise
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def advance(self):
        self._line = self._f.readline()
        self._lineNbr = 1
        while(self._line):
            # remove whitespace and EOL characters at the beginning and end of
            # line
            self._line = self._line.strip()
            
            # remove comments
            self._line = re.sub(r'\s*\/\/.*', '', self._line)
            
            # move to the next line if after comment removal we have an empty
            # string
            if not self._line:
                self._line = self._f.readline()
                self._lineNbr += 1
                continue
            
            #replace two or more white spaces with a single space
            self._line = re.sub('\s{2,}', ' ', self._line)

            return True
            
        self._f.close()
        return False
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : commandType
    # Description: Returns the type of the current VM command
    # Parameters : None
    # Returns    : C_ARITHMETIC  - if is an arithmetic command
    #              C_PUSH, C_POP - for push and pop commands respectively
    #              C_LABEL       - if it is a label
    #              C_GOTO, C_IF  - for goto and if commands respectively
    #              C_FUNCTION    - if it is a function command
    #              C_RETURN      - if it is a return command
    #              C_CALL        - if it is a call command
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def commandType(self):
        ret = None
        elements = re.split(r'\s+', self._line)
        
        if 1 == len(elements):
            if re.match(r'^return', elements[0]):
                ret = C_RETURN
            elif re.match(r'add|sub|neg|eq|gt|lt|and|or|not', elements[0]):
                ret = C_ARITHMETIC
            else:
                ret = C_UNKNOWN
        elif 2 == len(elements):
            if re.match(r'^label', elements[0]):
                ret = C_LABEL
            elif re.match(r'^goto', elements[0]):
                ret = C_GOTO
            elif re.match(r'^if-goto', elements[0]):
                ret = C_IF
            else:
                ret = C_UNKNOWN
        elif 3 == len(elements):
            if re.match(r'^function', elements[0]):
                ret = C_FUNCTION
            elif re.match(r'^call', elements[0]):
                ret = C_CALL
            elif re.match(r'push', elements[0]):
                ret = C_PUSH
            elif re.match(r'pop', elements[0]):
                ret = C_POP
            else:
                ret = C_UNKNOWN
        else:
            ret = C_UNKNOWN

        if C_UNKNOWN == ret:
            print('[Error] Unknown command type ' + element[0] + ' at line', self._lineNbr)
            sys.exit(1)

        return ret
                
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : arg1
    # Description: Returns the first argument of the current command. In the
    #              case of C_ARITHMETIC, the command itself is returned. Should
    #              not be called if the current command is C_RETURN
    # Parameters : None
    # Returns    : string - first argument of the command
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def arg1(self):
        elements = re.split(r'\s+', self._line)
        if C_ARITHMETIC == self.commandType():
            return elements[0]
        else:
            return elements[1]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : arg2
    # Description: Returns the second argument of the current command. Should be
    #              be called if the current command is C_PUSH, C_POP, C_FUNCTION
    #              or C_CALL
    # Parameters : None
    # Returns    : string - second argument of the command
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def arg2(self):
        elements = re.split(r'\s+', self._line)
        return elements[2]
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Name       : CodeWriter
# Description: Translates VM commands into Hack assembly code.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class CodeWriter(object):
    POINTER_BASE_ADDR = 3
    TEMP_BASE_ADDR = 5

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __init__
    # Description: Constructor. Opens the output file and gets ready to write
    #              into it.
    # Parameters : string : fileName - Path to the output file.
    # Returns    : Nothing.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, fileName):
        self.__f = open(fileName, 'w')
        self.__fileName = os.path.basename(fileName).rstrip('.asm')
        self.__functionName = fileName

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : setFileName
    # Description: Informs the code writer that the translation of a new VM is
    #              started.
    # Parameters : string : fileName - Path to the new .vm file.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setFileName(self, fileName):
        self.__fileName = os.path.basename(fileName).rstrip('.vm')
        self.__functionName = self.__fileName
            
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeArithmetic
    # Description: Writes assembly code that is translation of the given
    #              arithmetic command.
    # Parameters : string : command - arithmetic command
    # Returns    : Nothing.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeArithmetic(self, command):
        
        isUnary = False
        if re.match('neg|not', command):
            isUnary = True

        ret  = '// {}\n'.format(command)
        ret += self.__preArithCommandCode(isUnary=isUnary)
        
        if re.match('add', command):
            ret += 'M=D+M\n'
        elif re.match('sub', command):
            ret += 'M=M-D\n'
        elif re.match('neg', command):
            ret += 'M=-M\n'
        elif re.match('and', command):
            ret += 'M=D&M\n'
        elif re.match('or', command):
            ret += 'M=D|M\n'
        elif re.match('not', command):
            ret += 'M=!M\n'
        else: # lt, eq, gt
            ret += self.__lteqgt(command)

        # Increment the stack pointer.
        ret += self.__incSP()

        self.__f.write(ret)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeInit
    # Description: Writes assembly code that effects the VM initialization, also
    #              called bootstrap code. This code must be placed at the
    #              beginning of the output file.
    # Parameters : None.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeInit(self):
        res  = '// bootstrap code\n'
        # SP = 256
        res += '@256\n'
        res += 'D=A\n'
        res += '@SP\n'
        res += 'M=D\n'
        self.__f.write(res)

        # call Sys.init 0
        self.writeCall('Sys.init', 0)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writePushPop
    # Description: Writes the assembly code that is tha translation of the given
    #              command, where command is either C_PUSH or C_POP.
    # Parameters : int : command - C_PUSH or C_POP
    #              string : segment - name of the segment
    #              int : index - index of the segment
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writePushPop(self, command, segment, index):      
        if C_PUSH == command:
            ret = '// push {} {}\n'.format(segment, index)
            # Store base segement address into the A register.
            ret += self.__baseaddr(segment, index)
            
            # Static, constant, pointer, and temp segments are special cases.
            # They do not need this code. Calculate the base address of the
            # segement + offset.
            if not re.match('static|constant|pointer|temp', segment):
                if 0 == index:
                    ret += 'A=M\n'
                elif 1 == index:
                    ret += 'A=M\n'
                    ret += 'A=A+1\n'
                else: # index != 0 or index != 1
                    ret += 'D=M\n'
                    ret += '@' + str(index) + '\n'
                    ret += 'A=D+A\n'

            # Store the value of the segement[base address + offset]
            # into the D register.
            if not re.match('constant', segment):
                ret += 'D=M\n'

            # Push the value onto the stack
            ret += '@SP\n'
            ret += 'A=M\n'
            ret += 'M=D\n'
            
            # Increment the stack pointer
            ret += self.__incSP()
            
        # end: if C_PUSH == command
        
        else: # handle C_POP
            ret = '// pop {} {}\n'.format(segment, index)
            
            # Decrement the stack pointer.
            ret += '@SP\n'
            ret += 'M=M-1\n'
            
            # If we are popping the value off the stack into the 'constant'
            # segment we are simply decrementing the stack, which was done
            # in the two commands above. Hence no need to hande the 'constant'
            # segment.
            if not re.match('constant', segment):
                # Store the value from the stack into the D register. 
                ret += 'A=M\n'
                ret += 'D=M\n'

                # Store segment base address into the A register.
                ret += self.__baseaddr(segment, index)

                # 'static', 'pointer', and temp segments are special cases. They
                # do not require this code.
                # Calculate segment base address + offset and store the result
                # into the A register.
                if not re.match('static|pointer|temp', segment):
                    ret += 'A=M\n'
                    for i in range(index):
                        ret += 'A=A+1\n'

                # Pop the value off the stack into the
                # segement[base address + offset]
                ret += 'M=D\n'
                
        # end: else // handle C_POP

        self.__f.write(ret)
                
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : close
    # Description: Closes the output file
    # Parameters : None
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def close(self):
        self.__f.close()
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeLabel
    # Description: Writes assembly that effects the label command.
    # Parameters : string : label - Name of the label.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeLabel(self, label):
        res  = '// label {}\n'.format(label)
        res += '({}${})\n'.format(self.__functionName, label)
        self.__f.write(res)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeIf
    # Description: Writes assembly code that effects the if-goto command.
    # Parameters : string : label - Name of the label to go to
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeIf(self, label):
        ret = '// if {}\n'.format(label)
        # Decrement the stack pointer
        ret += '@SP\n'
        ret += 'M=M-1\n'

        # Pop the value off the stack and store it in D register.
        ret += 'A=M\n'
        ret += 'D=M\n'

        # Load the jump address into A register
        ret += '@{}${}\n'.format(self.__functionName, label)

        # Jump if the value in D is not equal to 0
        ret += 'D;JNE\n'

        # Write the result into the output file.
        self.__f.write(ret)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeGoto
    # Description: Writes assembly that effects the goto command.
    # Parameters : string : label - Name of the label to go to
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeGoto(self, label):
        ret  = '// goto {}\n'.format(label)
        ret += '@{}${}\n'.format(self.__functionName, label) 
        ret += '0;JMP\n'
        self.__f.write(ret)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeCall
    # Description: Writes assembly code that effects the call command.
    # Parameters : string : functionName - Name of the function to be called.
    #              int : numArgs - Number of arguments for the function.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeCall(self, functionName, numArgs):
        # Function must return to unique addresses, i.e. there can be more than
        # 2 calls to the same function, meaning that return address of each
        # call must be unique, hence the return label must be also unique.

        # Check if the __retAddrCnt has been declared before
        try:
            # If it has, then increment it
            self.__retAddrCnt += 1
        except AttributeError:
            # If it hasn't then create and set it to 0
            self.__retAddrCnt = 0
            
        returnAddrLabel = '{}$returnAddr{}'.format(functionName,
                                                   self.__retAddrCnt)

        res  = '// call {} {}\n'.format(functionName, numArgs)
        # push return-address, using the label declared above.
        # 1. Store return-address into D register.
        res += '@{}\n'.format(returnAddrLabel)
        res += 'D=A\n'
        # 2. Push the value onto the stack.
        res += '@SP\n'
        res += 'A=M\n'
        res += 'M=D\n'
        # 3. Increment the stack pointer.
        res += self.__incSP()
        
        # push LCL, Save LCL of the calling stack.
        # push ARG, Save ARG of the calling function.
        # push THIS, Save THIS of the calling function.
        # push THAT, Save THAT of the calling function.
        for val in ('LCL', 'ARG', 'THIS', 'THAT'):
            res += '// push {}\n'.format(val)
            res += self.__pushVal(val)

        # ARG = SP-numArgs-5, Reposition ARG
        # 1. Calculate SP-numArgs-5 and store the result in D register.
        res += '// ARG = SP-numArgs-5\n'
        res += '@SP\n'
        res += 'D=M\n'    
        if 0 != numArgs:
            res += '@{}\n'.format(numArgs)
            res += 'D=D-A\n'
        res += '@5\n'
        res += 'D=D-A\n'

        # 2. Store D register into ARG
        res += '@ARG\n'
        res += 'M=D\n'

        # LCL = SP, Reposition LCL
        res += '// LCL = SP\n'
        res += '@SP\n'
        res += 'D=M\n'
        res += '@LCL\n'
        res += 'M=D\n'

        # goto functionName, Transfer control.
        res += '// goto {}\n'.format(functionName)
        res += '@{}\n'.format(functionName)
        res += '0;JMP\n'

        # Declare label for the return address.
        res += '// declare label for the return address\n'
        res += '({})\n'.format(returnAddrLabel)

        self.__f.write(res)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeFunction
    # Description: Writes assembly code that effects the function command.
    # Parameters : string : functionName - Name of the function.
    #              int : numLocals - Number of local variables in the function.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeFunction(self, functionName, numLocals):
        res = '// function {} {}\n'.format(functionName, numLocals)
        # Declare a label for the function entry.
        res += '({})\n'.format(functionName)
        
        # Push 0 numLocal times onto the stack
        for i in range(numLocals):
            # Push 0 onto the stack
            res += '@SP\n'
            res += 'A=M\n'
            res += 'M=0\n'
            # Increment the stack pointer
            res += self.__incSP()

        # Write the result
        self.__f.write(res)
            
        # Set the function name to current function
        self.__functionName = functionName
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : writeReturn
    # Description: Writes assembly code that effects the return command.
    # Parameters : None.
    # Returns    : Nothing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def writeReturn(self):
        frame = '{}$FRAME'.format(self.__functionName)
        returnAddr = '{}$RET'.format(self.__functionName)

        # FRAME = LCL, FRAME is a temporary variable
        res  = '// return\n'
        res += '// FRAME = LCL\n'
        res += '@LCL\n'
        res += 'D=M\n'
        res += '@{}\n'.format(frame)
        res += 'M=D\n'

        # RET = *(FRAME-5), Put the return address in a temporary variable.
        res += '// RET = *(FRAME-5)\n'
        res += self.__offset(returnAddr, frame, 5)

        # *ARG = pop(), Reposition the return address for the caller.
        # Pop the value off the stack and store it in D register.
        # 1. Decrement the stack pointer
        res += '// *ARG=pop()\n'
        res += '@SP\n'
        res += 'M=M-1\n'
        # 2. Store the value at the stack pointer to D
        res += 'A=M\n'
        res += 'D=M\n'

        # Store D register into *ARG
        res += '@ARG\n'
        res += 'A=M\n'
        res += 'M=D\n'

        # SP = ARG + 1
        res += '// SP=ARG+1\n'
        res += '@ARG\n'
        res += 'D=M+1\n'
        res += '@SP\n'
        res += 'M=D\n'

        # THAT = *(FRAME-1), Restore THAT of the caller.
        res += '// THAT = *(FRAME-1)\n'
        res += self.__offset('THAT', frame, 1)
        
        # THIS = *(FRAME-2), Restore THIS of the caller.
        res += '// THIS = *(FRAME-2)\n'
        res += self.__offset('THIS', frame, 2)
        
        # ARG = *(FRAME-3), Restore ARG of the caller.
        res += '// ARG = *(FRAME-3)\n'
        res += self.__offset('ARG', frame, 3)

        # LCL = *(FRAME-4), Restore LCL of the caller.
        res += '// LCL = *(FRAME-4)\n'
        res += self.__offset('LCL', frame, 4)
        
        # goto RET
        res += '// goto RET\n'
        res += '@{}\n'.format(returnAddr)
        res += 'A=M\n'
        res += '0;JMP\n'

        # Write the result.
        self.__f.write(res)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __pushVal
    # Description: Generates code to push value stored at addr.
    # Parameters : string : addr - Address where the value to be pushed is
    #                stored.
    # Returns    : string : ret - Code for pushing.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __pushVal(self, addr):
        # 1. Load the value to be pushed into register D
        res  = '@{}\n'.format(addr)
        res += 'D=M\n'
        # 2. Push the value onto the stack.
        res += '@SP\n'
        res += 'A=M\n'
        res += 'M=D\n'
        # 3. Increments the stack pointer.
        res += self.__incSP()

        return res
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __offset
    # Description: Generates code that will store a value in one variable based
    #              on an offset from the other variable.
    #              resVar = *(offsetVar - offset)
    # Parameters : string : resVar - Name of the variable where resulting value
    #                will be stored.
    #              string : offsetVar - Name of the variable which will be used
    #                as a starting point for the offset.
    #              int : offset - Offset value.
    # Returns    : string : ret - Code for the offset.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __offset(self, resVar, offsetVar, offset):
        # resVar = *(offsetVar - offset)
        ret  = '@{}\n'.format(offsetVar)
        ret += 'D=M\n'
        ret += '@{}\n'.format(offset)
        ret += 'D=D-A\n'
        ret += 'A=D\n'
        ret += 'D=M\n'
        ret += '@{}\n'.format(resVar)
        ret += 'M=D\n'

        return ret
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __baseaddr
    # Description: Generates code for storing the base address of the segment
    #              into the A register.
    # Parameters : string : segment - Name of the segment.
    #              int : index - index into the segment.
    # Returns    : string : ret - code for storing the base address of the
    #                segment into the A register.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __baseaddr(self, segment, index):
        # Determine what segment we are using and store the segement's
        # address (not the base address) into the A register.
        ret = '@'
        if re.match('argument', segment):
            ret += 'ARG\n'
        elif re.match('local', segment):
            ret += 'LCL\n'
        elif re.match('static', segment):
            ret += self.__fileName + '.' + str(index) + '\n'
        elif re.match('constant', segment):
            # Constant segment is a special case.
            # Store the value of the constant into the A register.
            ret += str(index) + '\n'
            ret += 'D=A\n'
        elif re.match('this', segment):
            ret += 'THIS\n'
        elif re.match('that', segment):
            ret += 'THAT\n'
        elif re.match('pointer', segment):
            # 'pointer' segment is another special case.
            # Store addresses of THIS or THAT into the A register.
            ret += str(type(self).POINTER_BASE_ADDR + index) + '\n'
            
        else: # re.match('temp', segment):
            ret += str(type(self).TEMP_BASE_ADDR + index) + '\n'

        return ret
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __lteqgt
    # Description: Generates code for lt, eq, or gt commands.
    # Parameters : string : command - must be one of lt, eq or gt. It tells this
    #                method for which command the code should be generated.
    # Returns    : string : ret - assembly code for lt, eq or gt
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __lteqgt(self, command):
        
        # Because of the specifics of eq, lt, and gt commands I need to keep
        # a counter, which will be inserted into the labels
        try:
            self.__cnt
        except AttributeError:
            self.__cnt = 0
            
        ret  = 'D=M-D\n'
        ret += 'M=-1\n'
        lteqgt = command.upper()
        jump = 'J' + lteqgt
        lteqgt += str(self.__cnt)
        ret += '@' + lteqgt + '\n'        
        ret += 'D;' + jump + '\n'
        ret += '@SP\n'
        ret += 'A=M\n'
        ret += 'M=0\n'
        ret += '(' + lteqgt + ')\n'
    
        self.__cnt += 1

        return ret
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __incSP
    # Description: Generates code to increment the stack pointer.
    # Parameters : None.
    # Returns    : string : ret - Code to increment the stack pointer.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __incSP(self):
        ret  = '@SP\n'
        ret += 'M=M+1\n'
        return ret
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Name       : __preArithCommandCode
    # Description: Generates code that is common to all the arithmetic commands
    #              of a given type, which be inserted before each command.
    # Parameters : boolean : isUnary - if True the returned values will be
    #                common code generated for unary operations.
    # Returns    : string : ret - Common code which should be inserted before
    #                each arithmetic command.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __preArithCommandCode(self, isUnary=False):
        ret = ''
        
        if not isUnary:
            ret  = '@SP\n'
            ret += 'M=M-1\n'
            ret += 'A=M\n'
            ret += 'D=M\n'
            
        ret += '@SP\n'
        ret += 'M=M-1\n'
        ret += 'A=M\n'
        
        return ret
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main code
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main():
    fileList = [] # list of .vm files to process
    outputFileName = None # Full path to the output file.

    # Handle the case when input is a directory
    if os.path.isdir(sys.argv[1]):
        outputFileName = os.path.join(
            sys.argv[1], os.path.basename(sys.argv[1]))
        
        # In this case we need to form a list of all the .vm files
        tmpList = os.listdir(sys.argv[1])

        # Make sure that each element in that list is a full path to the file.
        for i in range(len(tmpList)):
            tmpList[i] = os.path.join(sys.argv[1], tmpList[i])

        # Extract only .vm files from the directory
        for el in tmpList:
            if os.path.isfile(el) and re.match(r'.*\.vm$', el):
                fileList.append(el)
                
    # end: if sys.argv[1] is a directory
    else: # sys.argv[1] is not a directory, but a lonely file path
        fileList.append(sys.argv[1])
        outputFileName = sys.argv[1].rstrip('.vm')

    # append .asm extension to the outputFileName
    outputFileName = outputFileName + '.asm'

    # Traverse each file and generate assembly code for it.
    codeWriter = None
    for fileName in fileList:
        # Instantiate CodeWriter.
        # It has to be instantiated only once.
        try:
            # If exception hasn't occurred then we already have instantiated
            # the CodeWriter and need to inform it that we are switching
            # to another file.
            codeWriter.setFileName(fileName)          
        except AttributeError:
            # If we caught an exception then CodeWriter hasn't been
            # instantiated yet, so let's instantiate it and write
            # bootstrap code into the output file.
            codeWriter = CodeWriter(outputFileName)
            codeWriter.writeInit()

        # For each file there is a new instance of the parser.
        parser = Parser(fileName)

        # Traverse the .vm file
        while(parser.advance()):
            # Write to the output file based on the command type
            commandType = parser.commandType()
            if C_ARITHMETIC == commandType:
                codeWriter.writeArithmetic(parser.arg1())
            elif C_PUSH == commandType or C_POP == commandType:
                codeWriter.writePushPop(commandType, parser.arg1(), int(parser.arg2()))
            elif C_IF == commandType:
                codeWriter.writeIf(parser.arg1())
            elif C_GOTO == commandType:
                codeWriter.writeGoto(parser.arg1())
            elif C_LABEL == commandType:
                codeWriter.writeLabel(parser.arg1())
            elif C_FUNCTION == commandType:
                codeWriter.writeFunction(parser.arg1(), int(parser.arg2()))
            elif C_RETURN == commandType:
                codeWriter.writeReturn()
            elif C_CALL == commandType:
                codeWriter.writeCall(parser.arg1(), int(parser.arg2()))
            else:
                raise Exception('Unrecognized command: {}'.format(commandType));

    # We are done going through all the input files. Close the output file.
    codeWriter.close()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Let's go ...
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if '__main__' == __name__:
    main()
