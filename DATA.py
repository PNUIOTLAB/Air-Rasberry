import bluepy.btle as btle

p = btle.Peripheral("20:20:1d:27:d1:17")
s = p.getServiceByUUID("19b10000-e8f2-537e-4f6c-d104768a1214")
c = s.getCharacteristics()[0]

c.write(bytes("0001".encode()))
p.disconnect()
