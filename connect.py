import bluetooth


Target_device_addr = "20:20:1d:27:d1:17"

port =1
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((Target_device_addr, port))
sock.send("hello")
sock.close
