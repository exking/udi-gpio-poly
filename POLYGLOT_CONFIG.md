## Configuration and setup
- Currently the only Custom Configuration Parameter to set:
    - key = GPIO_MODE
    - Valid "values": GPIO.BCM or GPIO.BOARD (default = GPIO.BOARD if nothing specified)
- This pertains to the pin numbers.  From <https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/>

>There are two ways of numbering the IO pins on a Raspberry Pi within RPi.GPIO. The first is using the BOARD numbering system. This refers to the pin numbers on the P1 header of the Raspberry Pi board. The advantage of using this numbering system is that your hardware will always work, regardless of the board revision of the RPi. You will not need to rewire your connector or change your code.

>The second numbering system is the BCM numbers. This is a lower level way of working - it refers to the channel numbers on the Broadcom SOC. You have to always work with a diagram of which channel number goes to which pin on the RPi board. Your script could break between revisions of Raspberry Pi boards.

#### For more pinout information:
- <https://www.raspberrypi.org/documentation/usage/gpio/>
- <https://pinout.xyz/pinout/wiringpi>
