import serial


class Connector:
	def __init__(self, configs):
		self.configs = configs

		self.serialPort = serial.Serial(
				self.configs['CONNECTER']['serial'], 
				int(self.configs['CONNECTER']['speed'])
			)

	def send(self, jsondata):
		self.serialPort.write(jsondata.encode())