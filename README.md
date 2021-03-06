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

Before a letter was typed, the rotors turned according to an
odometer-style system (but not quite due to something called _double
stepping_).  One important thing to note is that in a physical Enigma
machine, the mechanical movement of the key is what causes the rings
to move and this is what causes the turning to occur *before* the key
is encrypted.

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

To define an Enigma machine, we therefore need to define quite a lot
of structure.  Some is universal, such as the configurations of the
rotors and reflectors, but some is to do with the daily settings.
In total, we will use the following data structures:

```python
rotors       = {} # List of the individual rotors
notches      = {} # List of the notch positions for the rotors
reflectors   = {} # List of the individual reflectors
plugboard    = [] # List of the current plugboard setting
rings        = [] # List of the chosen rotors
ringSettings = [] # List of the ring settings
offsets      = [] # List of the offsets of the rings
reflector    = "" # Name of the current reflector
```

The first three are _universal_, the others depend on the daily and
message settings.
(Note that we're not being particularly picky on the python
distinction between a `list` and a `dict`.)

We will also make use of two subroutines that convert between letters
and numbers.
As we'll be working with mod 26 arithmetic, we want to
convert `A` to `0` and so on.  We'll also force uppercase.

```python
def encode(c):
    return ord(c.upper()) - 65

def decode(c):
    return chr(c + 65)
```

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

To define a rotor, we step through the characters in its definition
and record the differences.  We save this in the `rotors` list.

```python
def defineRotor(n,s):
    i = 0
    f = []
    for c in s:
        d = (encode(c) - i)%26
        f.append(d)
    rotors[n]  = f
```

We can then initialise the rotors.  For the **Enigma I** machine, we
would do this via:

```python
defineRotor("I",   "EKMFLGDQVZNTOWYHXUSPAIBRCJ")
defineRotor("II",  "AJDKSIRUXBLHWTMCQGZNPYFVOE")
defineRotor("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO")
defineRotor("IV",  "ESOVPZJAYQUIRHXLNFTGKDCMWB")
defineRotor("V",   "VZBRGITYUPSDNHLXAWMJQOFECK")
```

To apply a rotor, we need to know its current offset.  If the offset
is, say, `C` then this means that `A` first becomes `C` before being
fed into the rotor.  In practice, this means that we add the 3rd
"difference" to `A`.  The formula is therefore:

```
letter -> letter + rotor_difference_at_position(offset)
```

In our program, we'll store the choices of the current rings in the
list `rings`, the offsets in `offsets`, and the ring settings in
`ringSettings`.  It turns out that the ring settings apply in the
opposite direction to the offsets, also they start with the base
position at `1` rather than `0`.

```python
def applyRotor(n,c):
    r = rotors[rings[n]]
    o = (offsets[n] - (ringSettings[n]-1) + c)%26
    
    return (c + r[o]) % 26
```

In this, `n` is the name of the rotor and `c` the character (as a
number).  With no offset, we would apply the rotor at the character
`c`, but with an offset we step forward that number of stops.  This
might lead to "wrap around" which is why we have the inner `%26`.  The
rotor stores the _difference_ so this is added to the original
character, but again mod 26 to take into account wrap around.

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
def defineRotor(n,s):
    i = 0
    f = []
    r = [None]*26
    for c in s:
        d = (encode(c) - i)%26
        f.append(d)
        r[(i + d)%26] = (-d)%26
        i += 1
    rotors[n]  = [f, r]
```

Our rotor now consists of two lists of differences and so the code to
apply a rotor needs to take this into account.  The modified code for
this, where the `d` parameter is `0` for forward and `1` for reverse, is:

```python
def applyRotor(n,d,c):
    r = rotors[rings[n]]
    o = (offsets[n] - (ringSettings[n]-1) + c)%26
    
    return (c + r[d][o]) % 26
```

At this point, we might be a bit nervous about whether or not our code
works so a test function would seem like a good idea.  The following
encrypts an alphabet (which should return the _defining string_) and
then passes that through the reversed wheel (which should return the
alphabet back again).

```python
def testRotor(n):
    s = ""
    t = ""
    for i in range(26):
        c = applyRotor(n,0,i)
        s += decode(c)
        c = applyRotor(n,1,c)
        t += decode(c)
    return [s,t]
```

Note that we have to have set up the rings and the ring settings for
this to work.

#### Offsets and Alphabet Positions

The rotors consisted of two parts: the electrical system and the
alphabet ring.  These were separate and could be rotated with respect
to each other.  Part of the daily setting was how these were set.
These _ring settings_ were three numbers.  Examining the [picture of a
code book on
wikipedia](https://en.wikipedia.org/wiki/Enigma_machine#/media/File:Enigma_keylist_3_rotor.jpg)
shows that the numbers go from `1` to `26`.
Presuming that `1` means `A`, we need to subtract one from each of these in
our code, which we do when we apply a rotor.

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
def initialiseOffsets(s):
    global offsets
    offsets = []

    for c in s:
        offsets.append(encode(c))
```

(As we might call this several times, we overwrite the `offsets` globally.)

When encrypting a letter, we use *both* the offset and the alphabet
position.  What is also important to note is that the alphabet
position should be *subtracted* from the offset.

The offsets step each time a letter is encrypted.  When a lower ring
reaches a certain point, the next ring is also stepped.  The _notch_
that causes the next to turn depends on the alphabet ring and
therefore determined only by the offset, not the alphabet position.
The notches are different for different rotors, so we need a record of
the positions of the notches.
(Worth noting that later wheels had two notches.)
We can add this to the code that defines the rotors.

Note that there is a confusion of definitions on the relevant
Wikipedia pages as in some places the stepping position is recorded
according to the initial letter, and some according to the final letter.

So to step the rotors, we check the current position of each rotor
against the notches.  If a rotor is at its notch position, we note
that the next rotor should move.  _Double stepping_ means that the
current rotor should also move.  Interestingly, this makes the code
simpler because it means that a wheel never remains at its notch
position for more than one letter.  The physical wheels are positioned
so that the first ring is on the *right*, meaning that it is at the
end of the list.

```python
def stepOffsets():
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

We store the various reflectors in the dictionary `reflectors` and the
name of the one in use in the string `reflector`.

```python
def defineReflector(n,s):
    r = []
    for c in s:
        r.append(encode(c))
    reflectors[n] = r

def applyReflector(c):
    return reflectors[reflector][c]
```

### Plugboard

The plugboard is similar to the reflector in that it is static.  The
only difference is that it is specified by a series of two-letter
pairs.  A pair such as `EH` means that `E` becomes `H` and `H` becomes
`E`.  We assume that the pairs are separated by spaces.

```python
def definePlugboard(s):
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
    return plugboard[c]
```

### Encryption

The encryption process involves passing a letter through the
plugboard, the rings, the reflector, back through the rings, and back
through the plugboard.  In addition, the offsets must be stepped.

We start with the routine for encrypting a single character, which
includes converting it to a number and stepping the rotors (which
happend *before* the letter is encrypted).

```python
def encryptChar(c):
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
```

To apply this to a whole message, we simply do it character by character.

```python
def encryptMessage(s):
    e = []
    for c in s:
        e.append(encryptChar(c))
    return "".join(e)
```

(We could improve this slightly by stripping out non-encryptable
characters first.)

### Running the Code

To use this code, we need to start by initialising the machine.  The
"once for all" initialisation is to define the rotors and reflectors.

```python
defineRotor("I",   "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
defineRotor("II",  "AJDKSIRUXBLHWTMCQGZNPYFVOE", "E")
defineRotor("III", "BDFHJLCPRTXVZNYEIWGAKMUSQO", "V")
defineRotor("IV",  "ESOVPZJAYQUIRHXLNFTGKDCMWB", "J")
defineRotor("V",   "VZBRGITYUPSDNHLXAWMJQOFECK", "Z")

defineReflector("A", "EJMZALYXVBWFCRQUONTSPIKHGD")
defineReflector("B", "YRUHQSLDPXNGOKMIEBFZCWVJAT")
defineReflector("C", "FVPJIAOYEDRZXWGCTKUQSBNMHL")
```

When using the machine, we need to set the various configuration
settings.

```python
reflector = "B"
rings = ["I", "II", "III"]
ringSettings = [2,2,2]
definePlugboard("EJ OY IV AQ KW FX MT PS LU BD")
```

At this point we can encrypt a message:

```python
initialiseOffsets('AAA')
s = encryptMessage('ASECRETMESSAGE')
print(s)

initialiseOffsets('AAA')
print(encryptMessage(s))
```

We can test the machine against the Wikipedia page to ensure that at
least some of it is programmed correctly.  We are told that with no
plugboard, rings `I`, `II`, and `III`, reflector `B`, ring settings all `1`, and
initial offset `AAA`, then the string `AAAAA` should encrypt to
`BDZGO`.  Under the same conditions except for the ring settings being
`2`, we should get `EWTYX`.  (Note that the Wikipedia page gives the
ring settings as letters whereas the image of the code book gives them as
numbers.)
To test these, we try:

```python
reflector = "B"
rings = ["I", "II", "III"]
ringSettings = [1,1,1]
definePlugboard("")

initialiseOffsets('AAA')

s = encryptMessage('AAAAA')
print(s)

ringSettings = [2,2,2]
initialiseOffsets('AAA')
s = encryptMessage('AAAAA')
print(s)

```

Which produces:

```
BDZGO
EWTYX
```

as required.

## Google Sheets

The aim now is to rebuild this in a spreadsheet.  I use Google Sheets,
but this should work in any spreadsheet.  We'll use the same
principles as in the python implementation.  The first step is to load
the data into a spreadsheet.

### Initial Data

I've put each piece into a separate sheet, so that I have sheets named
`Rotors` and `Reflectors`.

#### Rotors

In the `Rotors` sheet, each
rotor consists of a row containing its name, its alphabet string, and
its notch position.  This looks like:

```
I	EKMFLGDQVZNTOWYHXUSPAIBRCJ	Q
```


#### Reflectors

We do something similar in the Reflectors sheet, so that a row looks like:

```
A	EJMZALYXVBWFCRQUONTSPIKHGD
```

#### Letters

For convenience, I've included a fourth sheet called `Letters`.  This
consists of three rows.  The first and third are the alphabet, from
`A` to `Z`.  The second is the numbers `0` to `25`.  The purpose of
this is to convert a letter to a number and back again using `hlookup`
instead of `code` and `char`.  This is purely pedagogical.

### Encryption

In setting up the encryption sheet, a certain balance has to be chosen
between simplicity and automation.  The choice of rings, for example,
can link directly to the location of their specification but only with
complicated expressions.  Rather, it is easier just to put the
location in the correct cells.  Similarly, an amount of
copy-and-pasting formula can be avoided by judicious use of
`arrayformula`, but again this makes them complicated.

The non-encryption part is set up with rows as follows:

```
Message
Ciphertext
Unknown Letter
Reflector
Rings
Plugboard
Notches
Ring Settings
Offsets
```

There are five blank rows after
`Rings` and a single blank row after each of `Plugboard` and `Notches`.
The `Unknown Letter` is used to substitute for any non-letter
character in the message.

To make the formulae for the rings and reflector a bit simpler, we
will put a row of the numbers `1` to `26` in cells `E3` to
`AD3`.  This is in the row `Unknown Letter` although it has nothing to
do with that.

#### Reflector

The cell next to the heading `Reflector` is where the name of the
reflector will go.  Next to this cell, we put the following formula
which looks up the reflector alphabet string:

```
=vlookup(B4,Reflectors!A1:B3,2)
```

In the second row, we want the letters spread out into cells and
converted to numbers.  For that, we use the formula:

```
=code(mid($C4,E$3,1))-65
```

and copy this across from `E4` to `AD4`.

This formula works as follows.  The `mid` formula is used to pick a
substring from some text.  The text is the alphabet string for the
reflector, which is in cell `C4`.  The starting position of the
substring is cell `E3`, and the length of the substring is `1`,
meaning that it picks up a single letter.  As this is copied across,
the dollars mean that cell `C4` doesn't change but `E3` does, so this
separates the alphabet string into one letter per cell.
Then the `code` formula converts that letter to a number, but such
that `A` becomes `65` (because it uses ASCII) so we subtract `65` so
that `A` becomes `0`.


#### Rotors

We do a similar thing with the rotors, starting with copying the
alphabet string.  But as we need to use the rotors in both directions,
each rotor needs two rows.  So we put the ring names in cells `B5`,
`B7`, and `B9`.  Then alongside them, we use the formulae:

```
=vlookup(B5,Rotors!A$1:B$5,2)
=vlookup(B7,Rotors!A$1:B$5,2)
=vlookup(B9,Rotors!A$1:B$5,2)
```

In the next rows, we want to produce the lists of the forward and
reverse lists of differences for this rotor.  This is achieved by the
following formulae (which should be copied across the rows):

```
=mod(code(mid($C5,E$3,1))-64 - E$3,26)
=mod(find(char(E$3+64),$C5) - E$3,26)
```

In this case, `$C5` refers to the cell containing the rotor
specification.

Let's break down one of these formulae.  We need to work from the inside out.

* `mid($C5,E$3,1)`: as in the reflector code, `mid()` selects some text from the middle of
  a given piece of text.  In this case, the text is in cell `C5`
  (i.e., the rotor specification).  The text is selected starting at
  the `E3` character and has length 1.  That is, it selects each
  character in the text in turn.
* `code(...)-64`: `code()` converts a letter into its ascii code.
  Subtracting 64 shifts this down so that `A` becomes `1`, `B` becomes
  `2`, and so on.
* `... - E$3`: if the original string had been `ABCDE...` then
  the result of the above manipulations would be the same as what is in
  `E3` so this subtraction finds the difference between the
  letter in the rotor specification and the position of that letter.
* `mod(...,26)`: this ensures that the number stays between 0 and 26.

The other thing we do with the rotors is to copy across the notch
position and convert it from a letter to a number.  
To get the notches, we put the following formulae in the row named
`Notches`:

```
=vlookup($B$5,Rotors!$A$1:$C$5,3)
=vlookup($B$7,Rotors!$A$1:$C$5,3)
=vlookup($B$9,Rotors!$A$1:$C$5,3)
```

Below each cell (say, in
`B13`), we put the formula `=code(B13)-65`.  This converts the letter to
a zero-based number (i.e., `A` becomes `0`).


#### Plugboard

The Plugboard needs two rows, the top of which consists
of the letters `A` to `Z`.  The lower row is where the user puts the
plugboard configuration: for a pair, say, `EH` put `H` underneath the
`E` and `E` underneath the `H`.  Any blank cells on the lower row
should be filled with the letter above it.

#### Encryption

Spreadsheets work on a different paradigm to ordinary programming.
Recursion is very limited.  So rather than a single set of offsets
that are continually updated, we have a set of offsets for each
letter.  Thus below the offsets we calculate the new offsets, and
continue this down the spreadsheet.  The formulae for the new offsets
are:

```
=mod(if(C16 = $C$14,B16+1,B16),26)
=mod(if(D16 = $D$14,C16+1,C16)+if(C16 =$C$14,1,0),26)
=mod(D8+1,26)
```

Remember that the rings are used from right to left.  The second `if`
in the formula for the middle ring is for double stepping.  Each
formula says, in essence, that if the previous ring matches its notch
then increment the current ring, else leave it as it was before.

These formulae should be copied down as far as needed.

Alongside these offsets go the various steps of the encryption.
Although it could be done in a single formula, not only does spacing
it out simplify it, it also makes it possible to see the inner
workings.

In addition to the encryption columns, it is useful to have an
indexing column with the numbers from `1` upwards.  I've put this in
the first column, under the heading `Offsets`.

The columns are as follows:

* `Plaintext`: This column contains the individual characters of the
  plaintext.
* `Prepared text`: The characters are then converted to upper case and
non-letters replaced by the `Unknown Letter`.
* `Plugboard`: The characters are passed through the plugboard using a
  lookup.
* `Numbers`: The rotors are more easily implemented using numbers so
at this stage the letters are converted to numbers.
* `Right-hand Ring`: Passing through the right-hand ring forwards.
* `Middle Ring`: Passing through the middle ring forwards.
* `Left-hand Ring`: Passing through the left-hand ring forwards.
* `Reflector`: Passing through the reflector.
* `Left-hand Ring`: Passing through the left-hand ring backwards.
* `Middle Ring`: Passing through the middle ring backwards.
* `Right-hand Ring`: Passing through the right-hand ring backwards.
* `Letters`: Now we convert the numbers back to letters.
* `Plugboard`: Last pass through the plugboard.

The formulae that achieve these steps are:

```
=mid($B$1,A17,1)
=if(iserror(find(upper(E17),"ABCDEFGHIJKLMNOPQRSTUVWXYZ")),$B$3,upper(E17))
=hlookup(F17,$E$11:$AD$11,2,false)
=hlookup(G17,Letters!$A$1:$Z$2,2,false)
=mod(H17 + index($E$9:$AD$9,1,mod(H17+D17-D$15+1,26)+1),26)
=mod(I17 + index($E$7:$AA$7,1,mod(I17+C17-C$15+1,26)+1),26)
=mod(J17 + index($E$5:$AA$5,1,mod(J17+B17-B$15+1,26)+1),26)
=index($E$4:$AD$4,1,K17+1)
=mod(L17 + index($E$6:$AD$6,1,mod(L17+B17-B$15+1,26)+1),26)
=mod(M17 + index($E$8:$AA$8,1,mod(M17+C17-C$15+1,26)+1),26)
=mod(N17 + index($E$10:$AA$10,1,mod(N17+D17-D$15+1,26)+1),26)
=hlookup(O17,Letters!$A$2:$Z$3,2,false)
=hlookup(P17,$E$11:$AD$11,2,false)
```

These then should be copied down as far as needed.

Finally, the ciphertext can be put together into a single cell using
the formula (for example, in cell `B2`):

```
=join("",Q17:Q)
```


