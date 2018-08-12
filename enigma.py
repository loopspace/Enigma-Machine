#! /usr/bin/python

rotors       = {}
notches      = {}
reflectors   = {}
plugboard    = []
offsets      = []
rings        = []
ringSettings = []
reflector    = ""

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

def defineRotor(n,s,c):
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
    rotors[n]  = [f, r]
    notches[n] = encode(c)

def applyRotor(n,d,c):
    '''
    Apply a rotor to a character

    :param int  n: the index of the rotor to apply
    :param int  d: the direction of the encryption
    :param int  c: the number corresponding to the charater

    :return: the number corresponding to the encrypted character
    '''

    r = rotors[rings[n]]
    o = offsets[n] - ringSettings[n]
    
    return (c + r[d][(o + c)%26]) % 26

def initialiseOffsets(s):
    '''
    Convert a string to a list of numbers

    :param str s: the string to convert
    '''
    global offsets
    offsets = []

    for c in s:
        offsets.append(encode(c))

def stepOffsets():
    '''
    Step the offsets according to the offsets and notches
    '''

    # Array of advances to be applied (to correctly handle double-stepping)
    a = [0] * len(rings)
    # Right-most ring always advances
    a[len(rings)-1] = 1
    for i in range(1,len(rings)):
        if offsets[i] == notches[rings[i]]:
            # current offset on ring i matches notch position
            # so we will advance ring i-1
            a[i-1] = 1
            # double stepping means that we also advance
            a[i] = 1
    for i in range(len(rings)):
        offsets[i] += a[i]
        offsets[i] %= 26

def defineReflector(n,s):
    '''
    Convert a reflector string into the reflector structure

    :param str n: the name of the reflector
    :param str s: the string specifying the reflector
    '''
    
    r = []
    for c in s:
        r.append(encode(c))
    reflectors[n] = r

def applyReflector(c):
    '''
    Encrypt a character using a reflector

    :param int  c: character to encrypt (as a number)
    :return: encrypted character (as a number)
    '''

    return reflectors[reflector][c]

def definePlugboard(s):
    '''
    Convert a plugboard string into the plugboard structure

    :param str s: the string specifying the plugboard
    :return: a array of encipherings
    '''
    global plugboard
    
    # Initialise
    plugboard = []
    for i in range(26):
        plugboard.append(i)

    # Split into pairs
    p = s.split()
    for c in p:
        a = encode(c[0])
        b = encode(c[1])
        plugboard[a] = b
        plugboard[b] = a

def applyPlugboard(c):
    '''
    Encrypt a character using the plugboard

    :param int  c: character to encrypt (as a number)

    :return: encrypted character (as a number)
    '''

    return plugboard[c]

def encryptChar(c):
    '''
    Encrypt a single character, stepping the offsets.

    :param int c: character to encrypt
    :return: encrypted character
    '''

    # Step rings
    stepOffsets()
    # Encode character
    d = encode(c)
    # Pass through plugboard
    d = applyPlugboard(d)
    # Pass through the rings, from right to left
    for i in range(len(rings)-1,-1,-1):
        d = applyRotor(i,0,d)
    # Apply the reflector
    d = applyReflector(d)
    # Pass back through the rings, from left to right
    for i in range(len(rings)):
        d = applyRotor(i,1,d)
    # Pass through the plugboard
    d = applyPlugboard(d)
    # Decode character
    d = decode(d)
    # Return character
    return d

def encryptMessage(s):
    e = []
    for c in s:
        e.append(encryptChar(c))
    return "".join(e)

def testRotor(n):
    '''
    Test a particular rotor

    :param int n: index of rotor to test
    '''

    s = ""
    t = ""
    for i in range(26):
        c = applyRotor(n,0,i)
        s += decode(c)
        c = applyRotor(n,1,c)
        t += decode(c)
    return [s,t]

def testReflector():
    '''
    Test the reflector
    '''

    s = ""
    t = ""
    for i in range(26):
        c = applyReflector(i)
        s += decode(c)
        c = applyReflector(c)
        t += decode(c)
    return [s,t]

def testPlugboard():
    '''
    Test the plugboard
    '''

    s = ""
    t = ""
    for i in range(26):
        c = applyPlugboard(i)
        s += decode(c)
        c = applyPlugboard(c)
        t += decode(c)
    return [s,t]


defineRotor("I",   "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
defineRotor("II",  "AJDKSIRUXBLHWTMCQGZNPYFVOE", "E")
defineRotor("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO", "V")
defineRotor("IV",  "ESOVPZJAYQUIRHXLNFTGKDCMWB", "J")
defineRotor("V",   "VZBRGITYUPSDNHLXAWMJQOFECK", "Z")

defineReflector("A", "EJMZALYXVBWFCRQUONTSPIKHGD")
defineReflector("B", "YRUHQSLDPXNGOKMIEBFZCWVJAT")
defineReflector("C", "FVPJIAOYEDRZXWGCTKUQSBNMHL")

reflector = "B"

rings = ["I", "II", "III"]
ringSettings = [2,2,2]
definePlugboard("")#"EJ OY IV AQ KW FX MT PS LU BD")

for i in range(len(ringSettings)):
    ringSettings[i] -= 1

initialiseOffsets('AAA')

for i in range(len(rings)):
    print(testRotor(i))

print(testReflector())
print(testPlugboard())

initialiseOffsets('AAA')
s = encryptMessage('AAAAA')
print(s)

initialiseOffsets('AAA')
print(encryptMessage(s))

