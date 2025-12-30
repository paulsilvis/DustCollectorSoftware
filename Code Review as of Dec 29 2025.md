# Overall status
- both lathe and saw gates operate correctly now
- access to pcf at 0x21 (relay board) is locked for task safety
- LEDs are not working correctly
- lathe and saw must be refactored into 3 files -- one for lathe, one for saw, and one common to both that contains the guts.
- LED implementation needs work -- it does not have a good balance between abstraction and implementation of policy
- Same goes for relay implementation -- see notes below.
- In general, I'd like to see better distinctions between low-level primitives, policy decisions and top-level control.  I want to see clear layers of abstraction / implementation, and better naming to reflect that (somehow).
  

## Notes
### Low Level Hardware Primitives

PCF8574

1. lPCF8574 objects -- one for LEDs, one for the 8-channel relay board that controls the Gates, and 3 for spares right now.
2. Each one has a LOCK.
3. We write BYTES to them, or read BYTES from them, atomically.

GATES
1. A Gate is implemented with two relays -- one to control the current to open, the other to close.  These are configured in an 'H-Bridge' manner, and it is absolutely essential that the two relays connected in this manner to a gate DO NOT get activated at the same time.  
2. A reasonable API for a Gate class is a constructor and a pair of functions:
   - open()
   - close()
3. The open() and close() operations for two different gates are executed asynchronously, so we must be careful to lock the appropriate section of code when doing so.  I think the lock in the PCF8754 will do this.
4. The constructor for a given Gate receives a reference to a singleton  PCF8574 object -- this will be the same object for each of 4 such Gate objects.  Each Gate is constructed with two bit-numbers -- one for open, and one for close.  Those bits control the appropriate relay pins on the 8-channel relay board.
5. CONSTRAINT:  the bits for open and close must NEVER both be set True. (that means, setting a 1 when writing to the I2C Bus that controls the relay board
6. The I2C digital expander routes bits to a ULN2803 8-bit chip that inverts the signal and outputs 3.3 for a 0 input and 0V for a 1 input.  Because the  -channel relay board is run on a 5V supply, we use jumpers on that board to configure it as 'active-low' and rely on the pullups to keep us out of trouble.  Repeat -- writing a '1' bit to the PCF8754 for the relays will provide a 0 bit as input to the given relay, which will activate it.
7. As noted above under Status, the code for Gate controllers is to be inside a single Gate object with its own bits for open and close, and maybe a name.  They all run exactly the same code as tasks.

LEDS
1. These are BITS.  There are 8 of them,numbered 0 - 7, controlled via PCF8574 at I2C address 0x20.  We read and write individual bits singly by specifying a bit position and a bit state.  The bit state is 1 to turn on, 0 to turn off.  The  LEDS class defines the bit positions with NAMES such as SAW_ON, SAW_OFF, LATHE_ON, etc.
2. Because the PCF8754 object that implements this behavior reads and writes BYTES, the operation of setting a bit to a given value (0 or 1) must be an atomic operation.  The current state of the 8 PCF8574 that drives the LEDs is maintained by that object.  A bit write is performed by copying the state, modifying  one or more bits in it, sending it via the PCF, and rewriting the new saved state, all within a LOCK owned by the PCF8574 base class.
3. The individual LEDs are connected  from the PCF to small resistor/transistor pairs such that lighting (turning on) an LED requires a 1 to be written (allows the transistor to conduct current from the 5V supply), and turning it off requires a 0.
4. note -- the current implementation tries to treat pairs of LEDs as semantically connected.  This is a policy decision that should be made higher up in the food chain.
5. A reasonable LEDs API might consist of a constructor that takes a PCF8574 object, initializes the bits to 0xff, and exports methods like:
   - on(bit_number)
   - off(bit_number)
   - all_on()
   - all_off()
   where bit-number is 0-7; the last two functions are just for convenience.

TASKS

-  There are 4 tasks handling gates, one each for saw, lathe, drill press and spare.  The main program creates the PCF8754 objects (1 for each I2C channel 0x20 through 0x24 and passes them to Gate controllers.
- There is 1 task for the ADC watcher, which periodically reads the 4 analog input channels and publishes appropriate messages (ON or OFF for a particular device).
- There are other tasks I won't go into here, but we'll get to them later.





	