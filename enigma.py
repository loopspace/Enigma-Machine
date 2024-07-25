#! /usr/bin/python

# Helpful functions for converting between letters and numbers
def encode(c):
    '''
    Convert a letter to a number, A -> 0 etc

    :param str c: the character to convert
    :return: the resulting number
    '''
    return ord(c.upper()) - 65

def decode(c):
    '''
    Convert a number to a letter, 0 -> A etc

    :param int c: the number to convert
    :return: the resulting character
    '''
    return chr(c + 65)

def prepareMessage(s,oc = "X"):
    e = []
    for c in s:
        if c.isalpha():
            e.append(c.upper())
        else:
            e.append(oc)
    return "".join(e)

def showMessage(s):
    e = []
    for i in range(len(s)):
        e.append(s[i])
        if i%5 == 4 and i != len(s) - 1:
            e.append(" ")
    return "".join(e)


class Enigma:

    # Rotors and reflectors are available to all machines
    rotors       = {} # List of the individual rotors
    reflectors   = {} # List of the individual reflectors
    notches      = {} # List of the notch positions for the rotors

    def __init__(self):
        self.debug = False
        self.notchesOverride = {} # Allow override of notch positions
        self.plugboard    = [] # List of the current plugboard setting
        self.rings        = [] # List of the chosen rotors
        self.ringSettings = [] # List of the ring settings
        self.offsets      = [] # List of the offsets of the rings
        self.reflector    = "" # Name of the current reflector
        self.stepOrder    = [] # Order to step the rings (Engima: 3,2,1; Pringles: 1,2,3)
        self.reflectorOffset = 0 # Allow for the reflector to have an offset

    @classmethod
    def defineRotor(cls,n,s,h):
        '''
        Convert a rotor string into the rotor structure

        :param str n: the name of this rotor
        :param str s: the string specifying the rotor
        :param str c: the location of the notch on this rotor
        :return: an array of arrays of differences
        '''

        i = 0
        f = []
        r = [None]*26
        for c in s:
            d = (encode(c) - i)%26
            f.append(d)
            r[(i + d)%26] = (-d)%26
            i += 1
            cls.rotors[n]  = [f, r]
            cls.notches[n] = encode(h)


    def overrideNotches(self,s):
        for i in range(len(s)):
            self.notches[self.rings[i]] = s[i]

    def applyRotor(self,n,d,c):
        '''
        Apply a rotor to a character

        :param int  n: the index of the rotor to apply
        :param int  d: the direction of the encryption
        :param int  c: the number corresponding to the charater

        :return: the number corresponding to the encrypted character
        '''

        r = self.rotors[self.rings[n]]
        o = (self.offsets[n] - (self.ringSettings[n]-1) + c)%26

        return (c + r[d][o]) % 26

    def initialiseOffsets(self,s):
        '''
        Convert a string to a list of numbers

        :param str s: the string to convert
        '''
        self.offsets = []

        for c in s:
            self.offsets.append(encode(c))


    def initialiseCan(self,k):
        '''
        Initialise using a keyword (simplified Pringles can)

        :param str k: the keyword to use
        '''
        o = encode(k[0]) # letter to align against
        self.reflectorOffset = (encode(k[len(k)-1]) - o)%26 # set the reflector offset
        k = list(k[1:-1])
        k.reverse()
    
        s = "" # decode( (encode(k[0]) - o - 1)%26 )
        for i in range(0,len(k)):
            s += decode( (encode(k[i]) - o -1)%26 )
        if self.debug:
            print(s)
        n = []
        for i in range(len(k)):
            n.append( (encode(k[i]) -o - 1)%26 )
        self.overrideNotches(n)
        self.initialiseOffsets(s)


    def initialiseStepOrder(self,s):
        '''
        Initialise the order in which the rotors are stepped, should be
        done after the rings are set.
        '''
        self.stepOrder = []
        if s == "Enigma":
            for i in range(len(self.rings)):
                self.stepOrder.insert(0,i)
        elif s == "Pringles":
            for i in range(len(self.rings)):
                self.stepOrder.append(i)
        elif type(s) == type([]):
            self.stepOrder = s
        else:
            for i in range(len(self.rings)):
                self.stepOrder.insert(0,i)

    def stepOffsets(self,):
        '''
        Step the offsets according to the offsets and notches
        '''

        # Array of advances to be applied (to correctly handle double-stepping)
        a = [0] * len(self.rings)
        # Right-most ring always advances
        a[ self.stepOrder[0] ] = 1
        for i in range(len(self.rings)-2,-1,-1):
            if self.rings[ self.stepOrder[i] ] in self.notchesOverride:
                n = self.notchesOverride[ self.rings[ self.stepOrder[i] ] ]
            else:
                n = self.notches[ self.rings[ self.stepOrder[i] ] ]
                
            if self.offsets[ self.stepOrder[i] ] == n:
                # current offset on ring i matches notch position
                # so we will advance ring i-1
                a[ self.stepOrder[i+1] ] = 1
                # double stepping means that we also advance
                a[ self.stepOrder[i] ] = 1
        for i in range(len(self.rings)):
            self.offsets[i] += a[i]
            self.offsets[i] %= 26

    @classmethod
    def defineReflector(cls,n,s):
        '''
        Convert a reflector string into the reflector structure

        :param str n: the name of the reflector
        :param str s: the string specifying the reflector
        '''

        r = []
        for c in s:
            r.append(encode(c))
            cls.reflectors[n] = r

    def applyReflector(self,c):
        '''
        Encrypt a character using a reflector

        :param int  c: character to encrypt (as a number)
        :return: encrypted character (as a number)
        '''

        return (self.reflectors[self.reflector][(c + self.reflectorOffset)%26] - self.reflectorOffset)%26

    def definePlugboard(self,s):
        '''
        Convert a plugboard string into the plugboard structure

        :param str s: the string specifying the plugboard
        :return: a array of encipherings
        '''
        
        # Initialise
        self.plugboard = []
        for i in range(26):
            self.plugboard.append(i)

        # Split into pairs
        p = s.split()
        for c in p:
            a = encode(c[0])
            b = encode(c[1])
            self.plugboard[a] = b
            self.plugboard[b] = a

    def applyPlugboard(self,c):
        '''
        Encrypt a character using the plugboard

        :param int  c: character to encrypt (as a number)

        :return: encrypted character (as a number)
        '''

        return self.plugboard[c]

    def encryptChar(self,c):
        '''
        Encrypt a single character, stepping the offsets.

        :param int c: character to encrypt
        :return: encrypted character
        '''
        s = [c]
        # Step rings
        self.stepOffsets()
        for o in self.offsets:
            s.append(o)
            # Encode character
        d = encode(c)
        s.append(d)
        # Pass through plugboard
        d = self.applyPlugboard(d)
        s.append(d)
        # Pass through the rings, from right to left
        for i in range(len(self.rings)-1,-1,-1):
            d = self.applyRotor(i,0,d)
            s.append(d)
            # Apply the reflector
        d = self.applyReflector(d)
        s.append(d)
        # Pass back through the rings, from left to right
        for i in range(len(self.rings)):
            d = self.applyRotor(i,1,d)
            s.append(d)
            # Pass through the plugboard
        d = self.applyPlugboard(d)
        s.append(d)
        # Decode character
        d = decode(d)
        s.append(d)
        # If debugging
        if self.debug:
            print(s)
            # Return character
        return d

    def encryptMessage(self,s):
        e = []
        for c in s:
            e.append(self.encryptChar(c))
        return "".join(e)


    def testRotor(self,n):
        '''
        Test a particular rotor

        :param int n: index of rotor to test
        '''

        s = ""
        t = ""
        for i in range(26):
            c = self.applyRotor(n,0,i)
            s += decode(c)
            c = self.applyRotor(n,1,c)
            t += decode(c)
        return [s,t]

    def testReflector(self):
        '''
        Test the reflector
        '''

        s = ""
        t = ""
        for i in range(26):
            c = self.applyReflector(i)
            s += decode(c)
            c = self.applyReflector(c)
            t += decode(c)
        return [s,t]

    def testPlugboard(self):
        '''
        Test the plugboard
        '''

        s = ""
        t = ""
        for i in range(26):
            c = self.applyPlugboard(i)
            s += decode(c)
            c = self.applyPlugboard(c)
            t += decode(c)
        return [s,t]

    def getOffsets(self):
        '''
        Return the current offsets as a string of letters
        '''

        r = []
        for s in self.offsets:
            r.append(decode(s))

        return "".join(r)

def definePringlesEnigma(k):

    can = Enigma()

    can.reflector = "P"
    can.rings = ["P3", "P2", "P1"]
    can.ringSettings = [1,1,1]
    can.definePlugboard("")
    can.initialiseStepOrder("Pringles")
    
    can.initialiseCan(k)
    return can

def encryptPringlesMessage(k,s):
    can = definePringlesEnigma(k)
    return can.encryptMessage(s)



Enigma.defineRotor("I",   "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
Enigma.defineRotor("II",  "AJDKSIRUXBLHWTMCQGZNPYFVOE", "E")
Enigma.defineRotor("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO", "V")
Enigma.defineRotor("IV",  "ESOVPZJAYQUIRHXLNFTGKDCMWB", "J")
Enigma.defineRotor("V",   "VZBRGITYUPSDNHLXAWMJQOFECK", "Z")

Enigma.defineReflector("A", "EJMZALYXVBWFCRQUONTSPIKHGD")
Enigma.defineReflector("B", "YRUHQSLDPXNGOKMIEBFZCWVJAT")
Enigma.defineReflector("C", "FVPJIAOYEDRZXWGCTKUQSBNMHL")

# Simplified Pringles Enigma Machine
#                         ABCDEFGHIJKLMNOPQRSTUVWXYZ
Enigma.defineRotor("P1", "CDEABGIFHLJMOKRNTUPQWSVZXY","Y")
Enigma.defineRotor("P2", "BADEFCIGHLMJKONQRPUSTYZVWX","Y")
Enigma.defineRotor("P3", "DABGHCEFJILKPMNOSTQRXYZUVW","Y")

#                            ABCDEFGHIJKLMNOPQRSTUVWXYZ
Enigma.defineReflector("P", "EDHBAILCFMOGJSKRUPNWQYTZVX")

# Test basic encryption (encrypted message generated by CyberChef)

machine = Enigma()

machine.reflector = "B"
machine.rings = ["I", "II", "III"]
machine.ringSettings = [2,2,2]
machine.definePlugboard("EJ OY IV AQ KW FX MT PS LU BD")

machine.initialiseOffsets('AAA')
machine.initialiseStepOrder("Enigma")

assert(
    showMessage(
        machine.encryptMessage(
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
            )
        ) == 'IFJED QVSYH UDLPN GOYPR ISWDI PZMZN ZMMPE EKILG KFEWU PZFGF GPYXT NXEJK WEJRF SMLHI YKHYX TMJCD VLOUG CXZZC HGENW RYSGO QOETB CKTVV YTZMW ROSVH UXVDB MIQCD NHMRO DKTBK ZROSD OTKQO CELJF XVFWQ PXTSJ QNTNT NZMHG WOIXS HGEVH PWUXL PCSHW KJJIH GZGWV NDUHP CJBZJ GCLJC JTZDF QIUEO NJBNN USSPX FCBIU TMIHZ WJNIY CVCNR PPNOR NPWRY EZJPZ DQYIX ETLBZ RWFIC MMSPL YQMMQ'
    )

# Test stepping (based on Wikipedia page)

stepTest = Enigma()
stepTest.reflector = "B"
stepTest.rings = ["I", "II", "III"]
stepTest.ringSettings = [2,2,2]
stepTest.definePlugboard("EJ OY IV AQ KW FX MT PS LU BD")

stepTest.initialiseStepOrder("Enigma")

# Single Step
stepTest.initialiseOffsets('AAU')

steps = []
for i in range(4):
    steps.append(stepTest.getOffsets())
    stepTest.encryptMessage('A')

assert(",".join(steps) == "AAU,AAV,ABW,ABX")

# Double Step    
stepTest.initialiseOffsets('ADU')

steps = []
for i in range(5):
    steps.append(stepTest.getOffsets())
    stepTest.encryptMessage('A')
    
assert(",".join(steps) == "ADU,ADV,AEW,BFX,BFY")

# Encryption and decryption 

jabberwock = Enigma()

jabberwock.reflector = "B"
jabberwock.rings = ["I", "II", "III"]
jabberwock.ringSettings = [2,2,2]
jabberwock.definePlugboard("")

jabberwock.initialiseOffsets('AAA')
jabberwock.initialiseStepOrder("Enigma")


jabberwock.initialiseOffsets('AAA')
s = prepareMessage('Twas brillig and the slithy toves did gyre and gimble in the wabe.  All mimsy were the borogroves and the mome raths outgabe.','X')

s = jabberwock.encryptMessage(s)

assert(showMessage(s) == "PATMA VTUJO TDLVQ TFXPV LAZFW DJSMG PIAWY SOOAN VCVIY RCOZD HEBCZ QVXGH ACJVM IPKEZ WTDXX WBCNS EWVDY MZXVD SQNTY UBFEF CHCLM HBWTZ VLVQA NKTHX ZWUNV")

## Pringle's Can Enigma

can = definePringlesEnigma("AAAAA")

assert(can.encryptMessage("ACE") == "LBV")
can.initialiseCan("AAAAA")
assert(can.encryptMessage("IVWYQDV") == "DECODED")

can.initialiseCan("AAAAA")
assert(can.encryptMessage("PVWZARCYHRRCKW") == "SECRETXMESSAGE")

can.initialiseCan("CYBER")
assert(can.encryptMessage('YPELONUPTOZS') == "CYBERXISXFUN")

can.initialiseCan("CODES")
assert(can.encryptMessage('hufvegz') == "AMERICA")
assert(encryptPringlesMessage('TUBES','actrqinxrnqlmvg') == "EXPLURIBUSXUNUM")

assert(encryptPringlesMessage('RADIO','yedwpqbubrjhwsetlhden') == "WHATXHATHXGODXWROUGHT")

assert(encryptPringlesMessage('CYBER','bvhftd') == "ENIGMA")

#debug=True
#print(encryptPringlesMessage('AAAAA','a' * 27**2))

print(encryptPringlesMessage('WILLO', prepareMessage('Beyond the Wild Wood comes the Wide World. And that’s something that doesn’t matter, either to you or me. I’ve never been there, and I’m never going, nor you either, if you’ve got any sense at all. Don’t ever refer to it again, please. Now then! Here’s our backwater at last, where we’re going to lunch.')))

print(encryptPringlesMessage('WILLO', 'COAMUIPVCFWPDEXTRFSKPISIHQYYFXEYCZYTOLBMAKZCPTUOBXZTHBUSNYSLCEADLEDGAXWXTMZAZHFRPDHBCYLSJUPOXPOEPCBGNQKFNNMWPHJDNMGNYQGKSWSFMMJOBNTMGOWHTJLZMFGXURFVUTJWQWVNNWDYVENPJIDMGDPSZLCQTINWXMBVLMVKNTXLGZBBUPTTFJGFCBIQHCGAXNUYNIPNEVDJNUHJSCGGNCTQFVLDDZAPZQADFCOVZFBMAPFKNDZXSWJUXTHZPVPVOZLNCABLUXITJPROZAXIWVYLWAP'))

print(encryptPringlesMessage('RATTY', prepareMessage('They glided up the creek, and the Mole shipped his sculls as they passed into the shadow of a large boat-house. Here they saw many handsome boats, slung from the cross beams or hauled up on a slip, but none in the water; and the place had an unused and a deserted air.')))

print(encryptPringlesMessage('RATTY', 'SCOICBVPKSHUROOSAJWFYJAJBBWKAUOUDCIQOZEOCOLICRDUJADUAPHMMCCLZWPPVCQFULVJAGPOTFUDAVNVSVTYKLMCJMNBOZBYOLWUTFSOZBCTQAYGVWCKSWWBATKXKOEEBMAZPHBEGLDYIJJZNSLCWCPMHTJWAYRNKXTLXBCCYTFQCEFVRHBTBRAVPVWSTXGHURGMDVUFOJCOUBBJSDKKLTVWRBOCJLIDYGKOABZKXEGWMDLPXYBQJIOMTTBIUZTWSAAOGFLW'))
