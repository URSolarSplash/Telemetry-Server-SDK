from .GenericSerialDevice import GenericSerialDevice
import pyvesc
import json
import time

class VescDevice(GenericSerialDevice):
	def __init__(self, cache, portName):
		super(VescDevice, self).__init__(cache, portName, 115200)
		self.lastWrite = time.time()
		self.writeRate = 0.1
	def update(self):
		if self.open:
			try:
				if (time.time() - self.lastWrite > self.writeRate):
					self.lastWrite = time.time()
					self.writeData()
				if self.port.in_waiting >= 71:
					# Check for new vesc message in the buffer
					(vescMessage, consumed) = pyvesc.decode(self.port.read(70))
					if vescMessage:
						if (self.cache.getNumerical("boatConfig",0) == 0):
							self.cache.set("motorTemp",float(vescMessage.temp_motor_filtered))
						self.cache.set("controllerTemp",float(vescMessage.temp_fet_filtered))
						self.cache.set("controllerInCurrent",float(vescMessage.avg_input_current))
						self.cache.set("controllerOutCurrent",float(vescMessage.avg_motor_current))
						self.cache.set("controllerDutyCycle",float(vescMessage.duty_cycle))
						self.cache.set("controllerRpm",float(vescMessage.rpm))
						self.cache.set("controllerInVoltage",float(vescMessage.v_in))
						#self.cache.set("vescFault",int(vescMessage.mc_fault_code))
			except Exception as e:
				print(e)
				self.close()
	def writeData(self):
		#Get the throttle value and write it to the vesc.
		# Throttle duty cycle value range for vesc: -100,000 to 100,000
		# Input throttle: 0 to 100
		# Only write a value if we are in endurance mode
		if (self.cache.getNumerical('boatConfig',0) == 0):
			throttle = ((self.cache.getNumerical('throttle',0)/255.0) * 100.0 * 1000.0)
		else:
			throttle = 0

		throttleMessage = pyvesc.SetDutyCycle(int(throttle))
		self.port.write(pyvesc.encode(throttleMessage))
		# Write value request
		self.port.write(pyvesc.encode_request(pyvesc.GetValues))
