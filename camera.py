import cv2
import time
import threading


class Camera:

	def __init__(self, configs, 
		camIndexList=[0], 
		aimSize=(30, 30), addingAimMarker=False):
		
		self.configs = configs
		self.addingAimMarker = addingAimMarker
		self.aimSize = aimSize

		self.camIndexList = [
			0, 
			f"rtsp://{self.configs['IPCAMERA']['login']}:{self.configs['IPCAMERA']['password']}@{self.configs['IPCAMERA']['ip']}:{self.configs['IPCAMERA']['port']}/Streaming/Channels/",
		]

		self.camIndex = 0
		self.cameraSource = self.camIndexList[self.camIndex] if len(self.camIndexList) > 0 else 0
		self.camera = cv2.VideoCapture(self.cameraSource)

		self.initConfigs()
		threading.Thread(target=self.getImgFromCamThread).start()


	def initConfigs(self):
		self.FPS = 1 / int(self.configs['CAMERA']['fps']) if self.configs['CAMERA']['fps'] != "0" else None
		self.RESOLUTION = (int(self.configs['CAMERA']['res']), int(self.configs['CAMERA']['res']))
		self.maxZoom = int(self.configs['CAMERA']['maxzoom'])

		self.baseImageWidth, self.baseImageHeight = self.RESOLUTION
		self.imageWidth, self.imageHeight = self.RESOLUTION
		self.aimSizeK = (self.imageWidth / self.aimSize[0], self.imageHeight /  self.aimSize[1])

		self.imageZoom = 1
		self.cameraFrame = None
		self.borderX, self.borderY = 0, 0

		self.CAMERA_WORKING = True
		self.cameraFrameNotUpdated = None


	def updateResolution(self, newRes):
		self.RESOLUTION = newRes
		self.baseImageWidth, self.baseImageHeight = self.RESOLUTION
		self.imageWidth, self.imageHeight = self.RESOLUTION
		self.aimSizeK = (self.imageWidth / self.aimSize[0], self.imageHeight /  self.aimSize[1])

		self.setNewImageSize()

	def changeCam(self):
		self.camIndex = self.camIndex + 1 if self.camIndex + 1 < len(self.camIndexList) else 0

		self.cameraSource = self.camIndexList[self.camIndex] if len(self.camIndexList) > 0 else 0
		self.camera = cv2.VideoCapture(self.cameraSource)
		
		self.initConfigs()


	def getOneFrame(self): return self.cameraFrame

	def setNewImageSize(self):
		if self.imageZoom > 1 and self.imageZoom <= self.maxZoom:
			self.borderX = round((self.baseImageWidth / self.maxZoom) * self.imageZoom)
			self.borderY = round((self.baseImageHeight / self.maxZoom) * self.imageZoom)

			self.imageWidth = self.baseImageWidth - (self.borderX * 2)
			self.imageHeight = self.baseImageHeight - (self.borderY * 2)


	def getImgFromCamThread(self):
		while self.CAMERA_WORKING:
			try:
				ifGet, cameraFrame = self.camera.read()
	
				if ifGet:
					cameraFrame = cv2.resize(cameraFrame, self.RESOLUTION, interpolation=cv2.INTER_AREA) # change a size (and adding reaolution)

					# adding zoom
					if self.imageZoom > 1 and self.imageZoom <= self.maxZoom:
						cameraFrame = cameraFrame[
								self.borderY:self.imageHeight + self.borderY, 
								self.borderX:self.imageWidth + self.borderX
							]

					# adding Aim
					if self.addingAimMarker:
						centerImagePos = (self.imageWidth / 2, self.imageHeight / 2)

						cv2.line(
							cameraFrame, 
							(round(centerImagePos[0]), round(centerImagePos[1] - (self.imageHeight / self.aimSizeK[1]))), # start pos
							(round(centerImagePos[0]), round(centerImagePos[1] + (self.imageHeight / self.aimSizeK[1]))), # finish pos
							(0, 0, 255),  # color
							2 # line width
						)
						cv2.line(
							cameraFrame, 
							(round(centerImagePos[0] - (self.imageWidth / self.aimSizeK[0])), round(centerImagePos[1])), # start pos
							(round(centerImagePos[0] + (self.imageWidth / self.aimSizeK[0])), round(centerImagePos[1])), # finish pos
							(0, 0, 255),  # color
							2 # line width
						)

					self.cameraFrame = cameraFrame

			except: pass


	def framesGeneratorGET(self):
		while True:
			if self.FPS: time.sleep(self.FPS)
			
			try:
				yield (
						b'--frame\r\n'
						b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', self.cameraFrame)[1].tobytes() + b'\r\n'
					)
			except Exception as error: 
				print(error)

				yield (
							b'--frame\r\n'
							b'Content-Type: image/jpeg\r\n\r\n'
						)