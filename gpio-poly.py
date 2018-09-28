#!/usr/bin/env python3

import polyinterface
import sys
import RPi.GPIO as GPIO
#import signal

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

    def stop(self):
        LOGGER.debug('Cleaning up GPIOs')
        GPIO.cleanup()

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
        self.pwm = None
        self.pwm_freq = 0
        self.pwm_dc = 0
        self.callback_set = False

    def start(self):
        try:
            self.pwm_dc = float(self.getDriver('GV1'))
        except:
            self.pwm_dc = 0
        try:
            self.pwm_freq = int(self.getDriver('GV2'))
        except:
            self.pwm_freq = 0
        self.updateInfo()

    def updateInfo(self):
        if self.callback_set:
            return True # updates are handled by callback functions
        self.mode = GPIO.gpio_function(self.pinid)
        self.setDriver('GV0', ISY_MODES[self.mode])
        self.setDriver('GV1', self.pwm_dc)
        self.setDriver('GV2', self.pwm_freq)
        self._reportSt()

    def _callback(self, channel):
        self._reportCb()

    def setMode(self, command):
        cmd = command.get('cmd')
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
        if self.pwm is not None:
            LOGGER.debug('Stopping PIN {} PWM'.format(self.pinid))
            self.pwm.stop()
            self.pwm = None
        if cmd in ['SET_INPUT', 'PULLUP', 'PULLDOWN']:
            self.mode = 1  # Input
            self.setDriver('GV0', ISY_MODES[self.mode])
            if cmd == 'PULLUP':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=50)
                self.callback_set = True
            elif cmd == 'PULLDOWN':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=50)
                self.callback_set = True
            else:
                GPIO.setup(self.pinid, GPIO.IN)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=50)
                self.callback_set = True
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
            LOGGER.error('setMode: Unrecognized command {}'.format(cmd))
            return False
        self.setup = True
        self._reportSt()
        return True

    def startPWM(self, command):
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
        query = command.get('query')
        self.pwm_dc = float(query.get('D.uom51'))
        self.pwm_freq = int(query.get('F.uom90'))
        self.setDriver('GV1', self.pwm_dc)
        self.setDriver('GV2', self.pwm_freq)
        self._pwm()
        return True

    def setPWM(self, command):
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
        cmd = command.get('cmd')
        if self.pwm is None:
            LOGGER.info('Pin {} is not in PWM mode'.format(self.pinid))
        if cmd == 'SET_DC':
            self.pwm_dc = float(command.get('value'))
            self.setDriver('GV1', self.pwm_dc)
            if self.pwm is not None:
                self.pwm.ChangeDutyCycle(self.pwm_dc)
        elif cmd == 'SET_FREQ':
            self.pwm_freq = int(command.get('value'))
            self.setDriver('GV2', self.pwm_freq)
            if self.pwm is not None:
                self.pwm.ChangeFrequency(self.pwm_freq)
        elif cmd == 'PWM':
            self._pwm()
        else:
            LOGGER.error('setPWM: Unrecognized command {}'.format(cmd))
            return False
        return True

    def _reportSt(self):
        if self.pwm is not None:
            self.setDriver('ST', 4)  # PWM
        elif self.mode in [0, 1] and self.setup:
            if GPIO.input(self.pinid):
                self.setDriver('ST', 2)  # High
            else:
                self.setDriver('ST', 1)  # Low
        else:
            self.setDriver('ST', 3)  # N/A

    def _reportCb(self):
        if GPIO.input(self.pinid):
            LOGGER.debug('Callback - High')
            self.reportCmd('DON')
            self.setDriver('ST', 2)  # High
        else:
            LOGGER.debug('Callback - Low')
            self.reportCmd('DOF')
            self.setDriver('ST', 1)  # Low

    def _pwm(self):
        LOGGER.info('Starting PIN {} PWM DC {} at {} Hz'.format(self.pinid, self.pwm_dc, self.pwm_freq))
        if self.pwm is not None:
            ''' PWM has already started '''
            self.pwm.ChangeFrequency(self.pwm_freq)
            self.pwm.ChangeDutyCycle(self.pwm_dc)
            return True
        if self.mode not in [0, 43] or self.setup is False:
            GPIO.setup(self.pinid, GPIO.OUT)
        self.mode = 43
        self.setDriver('GV0', ISY_MODES[self.mode])
        self.pwm = GPIO.PWM(self.pinid, self.pwm_freq)
        self.pwm.start(self.pwm_dc)
        self._reportSt()
        return True

    def query(self):
        self.updateInfo()
        self.reportDrivers()

    drivers = [{'driver': 'ST', 'value': 0, 'uom': 25},
               {'driver': 'GV0', 'value': 0, 'uom': 25},
               {'driver': 'GV1', 'value': 0, 'uom': 51},
               {'driver': 'GV2', 'value': 0, 'uom': 90}
              ]
    id = 'GPIO_PIN'
    commands = {
                    'DON': setMode, 'DOF': setMode, 'SET_INPUT': setMode,
                    'PULLUP': setMode, 'PULLDOWN': setMode, 'QUERY': query,
                    'PWMON': startPWM, 'SET_DC': setPWM, 'SET_FREQ': setPWM,
                    'PWM': setPWM
               }


#def signal_term_handler(signal, frame):
#    LOGGER.warning('Got SIGTERM, exiting...')
#    GPIO.cleanup()
#    sys.exit(0)


if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_term_handler)
    try:
        polyglot = polyinterface.Interface('GPIO')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
