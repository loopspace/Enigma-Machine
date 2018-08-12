# Programming an Enigma Machine

This is my attempt to program a simulation of an Enigma machine.  My
initial attempt will be in Python, but my goal is to make it work in a
Spreadsheet.

## Initial Design

An Enigma machine consists of:

1. A *plugboard*.  This is a monoalphabetic substitution cipher
   wherein a number of letters are connected in pairs.  In the wartime
   Enigma machine, ten pairings were made based on the daily
   settings.  The remaining letters were passed unchanged.
2. Three or more *rotors*.  Each rotor was a monoalphabetic
   substitution cipher.  The important part of the rotors was that
   they moved in a sort-of odometer style (but not exactly).  The
   choice of rotors and their starting positions was set by the
   daily settings, but were also determined on a per-message basis.
3. A *reflector*.  This is a monoalphabetic cipher in which the
   letters were paired.

The procedure for enciphering a letter was to send it through the
following ciphers:

1. The plugboard.
2. The first rotor.
3. The second rotor.
4. The third rotor.
5. The reflector.
6. The third rotor (in reverse).
7. The second rotor (in reverse).
8. The first rotor (in reverse).
9. The plugboard (in reverse).

(As a point of note, the plugboard (and reflector) were _self-inverse_.)

After a letter was typed, the rotors turned according to an
odometer-style system (but not quite due to something called _double
stepping_).

## Enigma Complexity

The number of starting configurations for the Enigma machine is rather
large.  What is interesting is that there are two parts to the
complexity: the plugboard and the rotors.

The plugboard is a straight-forward static substitution cipher.  As
such, it is susceptible to quite simple cryptanalysis (for example,
frequency analysis).  So although there are a phenominally large
number of possible settings for the plugboard, due to the encryption
method that number is not significantly large.

The rotors, on the other hand, form a polyalphabetic substitution
cipher.  The period of the cipher is long (26 x 25 x 26 -- the 25 is
due to the "double-stepping") so using standard attacks on periodic
substitution ciphers would not work as the message length is short.
Nevertheless, the key space is not actually that large and with 3
pre-determined rings (as in the original design), it is possible to
conduct a brute-force attack.

Combining the two -- the plugboard and the rotors -- seemingly enables
each to defend against the weakness of the other.  The large number of
settings of the plugboard appears to offset the small key space of the
rotors, while the polyalphabetic nature of the rotors appears to
negate the static nature of the plugboard.

The sheer genius of the Polish team, and later the British, was to
devise a method that effectively uncoupled the plugboard from the
rotors, allowing for a brute-force attack on the rotors followed by a
frequency analysis attack on the plugboard.

Although the introduction of extra rotors, and permutations thereof,
increased the key space of the rotors (and increased it to make
brute-force unfeasible), other weaknesses together with "cribs"
(informed guesses of the plaintext) meant that this remained a
feasible method of attack.

## Implementation

The first step in simulating an Engima machine is to set up the
structure for the plugboard and the rotors.
The plugboard has no initial structure but is completely determined by
the settings of the day.
The rotors have certain connections built in and it is only their
starting position that is set by the settings of the day.
So we start with the rotors.

### Rotors

The rotor settings can be found on the wikipedia page [Enigma Rotor
Details](https://en.wikipedia.org/wiki/Enigma_rotor_details), together
with the details of the reflectors.
They are listed as if they were monoalphabetic ciphers, but it is
important to remember that they rotate.

#### Initial Design

Rather than encode each rotor as a simple lookup table, therefore, it
is better to record the *offsets* for each letter.

Let us focus on the **Enigma I** machine, introduced in 1930.  Wikipedia
records its first rotor as `EKMFLGDQVZNTOWYHXUSPAIBRCJ`.  This means
that in its initial (`A`) position, `A` is encrypted as `E`.  After
one rotation, `A` enters into the `B` slot where it is encrypted as
`K`, but now `K` means `J` so `A` is encrypted as `J`.  The key point
is that the distance from `B` to `K` is the same as that from `A` to
`J`, so by recording these distances we save a fair amount of
computation.

To make life easy for ourselves, we'll write a function that takes the
description from the Wikipedia page and converts it into an array of
distances.  We'll do all our arithmetic mod 26.

We start with two useful subroutines that convert between letters and
numbers.  As we'll be working with mod 26 arithmetic, we want to
convert `A` to `0` and so on.  We'll also force uppercase.

```python
def encode(c):
    return ord(c.upper()) - 65

def decode(c):
    return chr(c + 65)
```

To define a rotor, we step through the characters in its definition
and record the offsets.

```python
def defineRotor(s):
    i = 0
    r = []
    for c in s:
        r.append((encode(c) - i)%26)
        i += 1
    return r
```

We can then initialise the rotors.  For the **Enigma I** machine, we
would do this via:

```python
rotors = {}
rotors["I"]   = defineRotor("EKMFLGDQVZNTOWYHXUSPAIBRCJ")
rotors["II"]  = defineRotor("AJDKSIRUXBLHWTMCQGZNPYFVOE")
rotors["III"] = defineRotor("BDFHJLCPRTXVZNYEIWGAKMUSQO")
```

To apply a rotor, we need to know its current offset.  If the offset
is, say, `C` then this means that `A` first becomes `C` before being
fed into the rotor.  In practice, this means that we add the 3rd
"difference" to `A`.  The formula is therefore:

```python
letter -> letter + rotor_difference_at_position(offset)
```

Or in python:

```python
def applyRotor(r,o,c):
    return (c + r[(o + c)%26]) % 26
```

In this, `r` is the rotor, `o` the offset, `c` the character (as a
number).  With no offset, we would apply the rotor at the character
`c`, but with an offset we step forward `o` stops.  This might lead to
"wrap around" which is why we have the inner `%26`.  The rotor stores
the _difference_ so this is added to the original character, but again
mod 26 to take into account wrap around.

#### Backwards

The rotors are applied twice, and in different directions.  We
therefore need to be able to apply them backwards as well as
forwards.  The simplest way to do this is to construct a reverse of
the rotor as we define it.

Recall that we've constructed the rotor by computing differences.  So
for rotor `I`, `C` becomes `M` which means that we record the
difference (`10`) in the third slot (corresponding to `C`) in the
list.  For the reverse, we need to record the opposite difference
(`-10`, which is `16` as we're working mod 26) but in the thirteenth
slot (corresponding to `M`).  The tricky part is that we don't fill
the slots in the reverse list in order, so we need to be careful with
that.

The modified code is:

```python
def defineRotor(s):
    i = 0
    f = []
    r = [None]*26
    for c in s:
        d = (encode(c) - i)%26
        f.append(d)
        r[(i + d)%26] = (-d)%26
        i += 1
    return [f, r]
```

Our rotor now consists of two lists of differences and so the code to
apply a rotor needs to take this into account.  The modified code for
this is:

```python
def applyRotor(r,o,d,c):
    return (c + r[d][(o + c)%26]) % 26
```

At this point, we might be a bit nervous about whether or not our code
works so a test function would seem like a good idea.  The following
encrypts an alphabet (which should return the _defining string_) and
then passes that through the reversed wheel (which should return the
alphabet back again).

```python
def testRotor(r):
    s = ""
    t = ""
    for i in range(26):
        c = applyRotor(rotors[r],0,0,i)
        s += decode(c)
        d = applyRotor(rotors[r],0,1,c)
        t += decode(d)
    return [s,t]
```

#### Offsets and Alphabet Positions

The rotors consisted of two parts: the electrical system and the
alphabet ring.  These were separate and could be rotated with respect
to each other.  Part of the daily setting was how these were set.
These _ring settings_ were three numbers.  Examining the [picture of a
code book on
wikipedia](https://en.wikipedia.org/wiki/Enigma_machine#/media/File:Enigma_keylist_3_rotor.jpg)
shows that the numbers go from `1` to `26`.
Presuming that `1` means `A`, we need to subtract one from each of these in
our code.

Along with the rotors, we need to keep track of the offsets and "step"
them accordingly after each letter is encrypted.
We need as many offsets as there are rotors, so a simple list of
offsets will do.
The stepping routine needs to be separate to the application routine
since the rotors are used twice in each encryption (once forward and
once backward).

The initial offsets will depend on which Enigma machine is being
emulated.  The early ones had an initial offset specified in the daily
setting, which would then be modified based on a key decided by the
sender.  The later ones had both the initial and message offsets set
by the sender.

The initial offsets were specified by a three-letter code, so we need
a subroutine that transforms that into the actual offsets.  This is
simple enough:

```python
def initialiseOffset(s):
    r = []
    for c in s:
        r.append(encode(c))
    return r
```

When encrypting a letter, we use *both* the offset and the alphabet
position.  What is also important to note is that the alphabet
position should be *subtracted* from the offset.

The offsets step each time a letter is encrypted.  When a lower ring
reaches a certain point, the next ring is also stepped.  The _notch_
that causes the next to turn depends on the alphabet ring and
therefore determined only by the offset, not the alphabet position.
The notches are different for different rotors, so we need a record of
the positions of the notches.

Note that there is a confusion of definitions on the relevant
Wikipedia pages as in some places the stepping position is recorded
according to the initial letter, and some according to the final letter.

```python
notch = {}
notch["I"]   = "Q"
notch["II"]  = "E"
notch["III"] = "V"
notch["IV"]  = "J"
notch["V"]   = "Z"
```

(Later wheels had two notches.)

So to step the rotors, we check the current position of each rotor
against the notches.  If a rotor is at its notch position, we note
that the next rotor should move.  _Double stepping_ means that the
current rotor should also move.  Interestingly, this makes the code
simpler because it means that a wheel never remains at its notch
position for more than one letter.  The physical wheels are positioned
so that the first ring is on the *right*, meaning that it is at the
end of the list.

```python
def stepOffsets(o,r,n):
    a = [0] * len(r)
    a[len(r)-1] = 1
    for i in range(1,len(r)):
        if o[i] == n[r][i]:
            a[i-1] = 1
            a[i] = 1
    for i in range(len(r)):
        o[i] += a[i]
        o[i] %= 26
```

In the code, we delay the actual stepping until the end so that the
comparison is always with the *current* position of the wheels.

To handle rotors with two notches, we could convert the notches for a
rotor into a list of notches and use the python syntax `in` to test if
the current position is in the list of that rotor's notches.

### Reflector

The reflector is a static part of the machine so is nowhere near as
complicated as the rotors.  The Wikipedia page about the rotors also
contains the details of the reflectors.  As these are static and only
used in one direction, we can simplify their implementation.

```python
def defineReflector(s):
    r = []
    for c in s:
        r.append(encode(c))
    return r

def applyReflector(r,c):
    return r[c]
```

### Plugboard

The plugboard is similar to the reflector in that it is static.  The
only difference is that it is specified by a series of two-letter
pairs.  A pair such as `EH` means that `E` becomes `H` and `H` becomes
`E`.  We assume that the pairs are separated by spaces.

```python
def definePlugboard(s):
    r = []
    for i in range(26):
        r.append(i)

    p = s.split()
    for c in p:
        a = encode(c[0])
        b = encode(c[1])
        r[a] = b
        r[b] = a
    return r

def applyPlugboard(r,c):
    return r[c]
```

### Encryption

The encryption process involves passing a letter through the
plugboard, the rings, the reflector, back through the rings, and back
through the plugboard.  In addition, the offsets must be stepped.  One
important thing to note is that in a physical Enigma machine, the
mechanical movement of the key is what causes the rings to move and
this occurs *before* the key is encrypted.