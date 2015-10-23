#!/usr/bin/python

import Adafruit_DHT	

import sys, getopt

def main(argv):

    sensor = Adafruit_DHT.AM2302
    pin = 23

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    try:
       opts, args = getopt.getopt(argv,"th",)
    except getopt.GetoptError:
      print 'am2302 -t|-h'
      sys.exit(2)
    for opt, arg in opts:
      if opt == '-t':
        if temperature is not None:
           print '{0:0.1f}'.format(temperature)
           sys.exit()
      if opt == '-h':
        if humidity is not None:
          print '{0:0.1f}'.format(humidity)
          sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])

