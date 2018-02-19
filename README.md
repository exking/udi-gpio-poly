# UDI Polyglot v2 GPIO Control Poly

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/exking/udi-gpio-poly/blob/master/LICENSE)

This Poly provides an interface between [Raspberry Pi GPIO](https://www.raspberrypi.org/documentation/usage/gpio-plus-and-raspi2/) header and [Polyglot v2](https://github.com/UniversalDevicesInc/polyglot-v2) server.

### Installation instructions
Make sure that you have a `zip` executable on the system, install using your OS package manager if necessarily.
You can install NodeServer from the Polyglot store or manually running
```
cd ~/.polyglot/nodeservers
git clone https://github.com/exking/udi-gpio-poly.git GPIO
cd GPIO
./install.sh
```
Make sure that user you run Polyglot as is a member of `gpio` group (user `pi` typically is).

### Notes

Please report any problems on the UDI user forum.

Thanks and good luck.
