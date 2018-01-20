#!/usr/bin/env python3

import polyinterface
import sys
import RPi.GPIO as GPIO

# These are physical PIN number
GPIO_PINS = [3,5,7,8,10,11,12,13,15,16,18,19,21,22,23,24,26,29,31,32,33,35,36,37,38,40]

# Logical GPIO numbers, aka BCM numbers
GPIO_PORTS = [2,3,4,17,27,22,10,9,11,5,6,13,19,26,14,15,18,23,24,25,8,7,12,16,20,21]

# GPIO port mode dictionary
PORT_MODE = {0: 'GPIO.OUT', 1: 'GPIO.IN', 40: 'GPIO.SERIAL', 
             41: 'GPIO.SPI', 42: 'GPIO.I2C', 43: 'GPIO.HARD_PWM', -1: 'GPIO.UNKNOWN'}

GPIO_MODE = GPIO.BOARD

LOGGER = polyinterface.LOGGER

# GPIO mode to ISY mode id
ISY_MODES = {0: 1, 1: 2, 40: 3, 41: 4, 42: 5, 43: 6, -1: 7}

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        self.name = 'GPIO Header'
        self.address = 'rpigpiohdr'
        self.primary = self.address

    def start(self):
        LOGGER.info('Started GPIO Pin controller')
        GPIO.setmode(GPIO_MODE)
        LOGGER.debug(GPIO.RPI_INFO)
        self.discover()

    def shortPoll(self):
        for node in self.nodes:
            self.nodes[node].updateInfo()
            
    def updateInfo(self):
        pass

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, command=None):
        for i in GPIO_PINS:
            address = 'gpiopin'+str(i)
            name = 'Pin '+str(i)
            if not address in self.nodes:
                self.addNode(GPIOpin(self, self.address, address, name, i))

    id = 'GPIO_HDR'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]


class GPIOpin(polyinterface.Node):
    def __init__(self, controller, primary, address, name, pinid):
        super().__init__(controller, primary, address, name)
        self.pinid = pinid
        self.mode = None
        self.st = None
        self.setup = False

    def start(self):
        self.updateInfo()

    def updateInfo(self):
        self.mode = GPIO.gpio_function(self.pinid)
        self.setDriver('GV0', ISY_MODES[self.mode])
        self._reportSt()

    def setMode(self, command):
        cmd = command.get('cmd')
        if cmd in ['SET_INPUT', 'PULLUP', 'PULLDOWN']:
            self.mode = 1  # Input
            self.setDriver('GV0', ISY_MODES[self.mode])
            if cmd == 'PULLUP':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            elif cmd == 'PULLDOWN':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            else:
                GPIO.setup(self.pinid, GPIO.IN)
        elif cmd in ['DON', 'DOF']:
            if self.mode != 0 or self.setup is False:  # Output
                self.mode = 0
                self.setDriver('GV0', ISY_MODES[self.mode])
                GPIO.setup(self.pinid, GPIO.OUT)
            if cmd == 'DON':
                GPIO.output(self.pinid, GPIO.HIGH)
            else:
                GPIO.output(self.pinid, GPIO.LOW)
        else:
            LOGGER.error('Unrecognized command {}'.format(cmd))
            return False
        self.setup = True
        self._reportSt()
        return True

    def _reportSt(self):
        if self.mode in [0, 1] and self.setup:
            if GPIO.input(self.pinid):
                self.setDriver('ST', 2)  # High
            else:
                self.setDriver('ST', 1)  # Low
        else:
            self.setDriver('ST', 3)  # N/A

    def query(self):
        self.updateInfo()
        self.reportDrivers()

    drivers = [{'driver': 'ST', 'value': 0, 'uom': 25},
               {'driver': 'GV0', 'value': 0, 'uom': 25}
              ]
    id = 'GPIO_PIN'
    commands = {
                    'DON': setMode, 'DOF': setMode, 'SET_INPUT': setMode,
                    'PULLUP': setMode, 'PULLDOWN': setMode, 'QUERY': query
               }


class HWInterface(polyinterface.Interface):
    """ Just to override the stop method """
    def stop(self):
        LOGGER.debug('Cleaning up GPIOs')
        GPIO.cleanup()
        super().stop()


if __name__ == "__main__":
    try:
        polyglot = HWInterface('GPIO')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        sys.exit(0)
