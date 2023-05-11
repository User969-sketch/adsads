from flask import Flask, render_template, Response, request
import threading
import cv2
import random
import socket
import time

import connector
import camera
#import checkimagefield




class MainApp:
	def __init__(self, configs, appName=__name__):
		self.configs = configs
		self.ID = self.createID()
		self.Camera = camera.Camera(configs)
		self.CheckerForAutoAim = checkimagefield.AimMarkerCheck()

		self.ifControlMenu = False

		if self.configs['SERVER']['ip'] == 'auto': self.configs['SERVER']['ip'] = socket.gethostbyname(socket.gethostname())

		self.__ServerApp = Flask(appName)
		# self.Connector = connector.Connector(configs)

		self.screenWidth, self.screenHeight = None, None
		self.MainMarkerCord = [None, None]
		self.NewMarkerCord = None
		self.ifAutoAimAvaliable = True

		self.gunsButtonStatus = {
			'guncontrolbtn_ltop': False,
			'guncontrolbtn_top': False,
			'guncontrolbtn_rtop': False,
			'guncontrolbtn_left': False,
			'guncontrolbtn_right': False,
			'guncontrolbtn_lbottom': False,
			'guncontrolbtn_bottom': False,
			'guncontrolbtn_rbottom': False
		}

	def createID(self, letters='abcdefghijklmnopqrstuvwxyz1234567890_'):
		return ''.join([random.choice(list(letters)).upper() for i in range(3)]) + '_' + ''.join([random.choice(list(letters)).upper() for i in range(2)])


	def moveForAutoAim(self, controlFrame, controlFrameSize, 
						nowMarkerCords, markerToMove1, markerToMove2,
						marketToMoveField1, marketToMoveField2,
						marketToMoveFieldVector1, marketToMoveFieldVector2):
		self.ifAutoAimAvaliable = False

		marketToMoveFieldSize1 = self.CheckerForAutoAim.getImageSize(marketToMoveField1)
		marketToMoveFieldKeypoints1 = self.CheckerForAutoAim.getKeyPoints(marketToMoveField1)
		marketToMoveFieldSize2 = self.CheckerForAutoAim.getImageSize(marketToMoveField2)
		marketToMoveFieldKeypoints2 = self.CheckerForAutoAim.getKeyPoints(marketToMoveField2)

		correctResultC = 0
		nowMarkerStartPos = (
				nowMarkerCords[0] - marketToMoveFieldVector1[0], 
				nowMarkerCords[1] - marketToMoveFieldVector1[1]
			)
		nowMarkerEndPos = (
				nowMarkerCords[0] + marketToMoveFieldVector1[2], 
				nowMarkerCords[1] + marketToMoveFieldVector1[3]
			)

		while True:
			if correctResultC > 7: time.sleep(10); break
			# if nowMarkerCords[0] > markerToMove1[0]: print('left')
			# elif nowMarkerCords[0] < markerToMove1[0]: print('right')

			newFrame = self.Camera.getOneFrame()

			nowMarkerField = self.CheckerForAutoAim.changeNewMarkerFieldSize(
				newFrame, controlFrameSize, 
				nowMarkerCords,
				startPos=nowMarkerStartPos, endPos=nowMarkerEndPos
			)[0]

			nowMarkerKeypoints = self.CheckerForAutoAim.getKeyPoints(nowMarkerField)
			# nowMarkerFieldSize = self.CheckerForAutoAim.getImageSize(nowMarkerField)

			result = self.CheckerForAutoAim.checkPoints(
					nowMarkerKeypoints, marketToMoveFieldKeypoints1,
					controlFrameSize, marketToMoveFieldSize1
				)


			if result > 0:
				correctResultC += 1
			else: correctResultC = 0


		correctResultC = 0
		nowMarkerStartPos = (
				nowMarkerCords[0] - marketToMoveFieldVector2[0], 
				nowMarkerCords[1] - marketToMoveFieldVector2[1]
			)
		nowMarkerEndPos = (
				nowMarkerCords[0] + marketToMoveFieldVector2[2], 
				nowMarkerCords[1] + marketToMoveFieldVector2[3]
			)

		while True:
			if correctResultC > 15: break

			if nowMarkerCords[1] > markerToMove1[1]: print('top')
			elif nowMarkerCords[1] < markerToMove1[1]: print('bottom')

			newFrame = self.Camera.getOneFrame()

			nowMarkerField = self.CheckerForAutoAim.changeNewMarkerFieldSize(
				newFrame, controlFrameSize, 
				nowMarkerCords,
				startPos=nowMarkerStartPos, endPos=nowMarkerEndPos
			)[0]

			nowMarkerKeypoints = self.CheckerForAutoAim.getKeyPoints(nowMarkerField)
			# nowMarkerFieldSize = self.CheckerForAutoAim.getImageSize(nowMarkerField)

			result = self.CheckerForAutoAim.checkPoints(
					nowMarkerKeypoints, marketToMoveFieldKeypoints2,
					controlFrameSize, marketToMoveFieldSize2
				)


			if result > 0:
				correctResultC += 1
				print(f'C2: {correctResultC}')
			else: correctResultC = 0


		self.ifAutoAimAvaliable = True

	def start(self):

		@self.__ServerApp.route('/')
		def index():
			if self.ifControlMenu:
				return render_template('index.html', ID=self.ID, imgscale=f"transform: scale({self.configs['CAMERA']['scale']}, 1)") # transf = 1 OR -1
			return render_template('index_withoutcontrol.html', ID=self.ID, imgscale=f"transform: scale({self.configs['CAMERA']['scale']}, 1)")

		@self.__ServerApp.route('/openclosecontrolmenu')
		def openclosecontrolmenu():
			self.ifControlMenu = not self.ifControlMenu

			if self.ifControlMenu:
				self.screenWidth, self.screenHeight = int(request.args.get('width')), int(request.args.get('height'))
				self.MainMarkerCord = [self.screenWidth / 2, self.screenHeight / 2]
				self.Camera.updateResolution((self.screenWidth, self.screenHeight))

			return '<script>window.location.href = "/";</script>'

		@self.__ServerApp.route('/videostream')
		def videostream(): 
			return Response(
					self.Camera.framesGeneratorGET(), 
					mimetype='multipart/x-mixed-replace; boundary=frame'
				)

		@self.__ServerApp.route('/move')
		def gotocommand():
			return '', 200, {'Content-Type': 'text/plain'}


		@self.__ServerApp.route('/firebuttonact')
		def firebutton():
			# self.Connector.send('{"command":"fire"}')
			return '', 200, {'Content-Type': 'text/plain'}


		@self.__ServerApp.route('/changecamdefbutton')
		def changecamdef():
			self.Camera.changeCam()
			# self.Connector.send('{"command":"camprotectchange"}')
			return '', 200, {'Content-Type': 'text/plain'}

		# ZOOM PART
		@self.__ServerApp.route('/camzoomplus')
		def camzoomplus():
			self.Camera.imageZoom = self.Camera.imageZoom + float(self.configs['CAMERA']['zoomadd'])
			if self.Camera.imageZoom > int(self.configs['CAMERA']['maxzoom']) - 1: self.Camera.imageZoom = int(self.configs['CAMERA']['maxzoom'])

			self.Camera.setNewImageSize()
			
			return '', 200, {'Content-Type': 'text/plain'}

		@self.__ServerApp.route('/camzoomminus')
		def camzoomminus():
			self.Camera.imageZoom = self.Camera.imageZoom - float(self.configs['CAMERA']['zoomadd'])
			if self.Camera.imageZoom < 1: self.Camera.imageZoom = 1

			self.Camera.setNewImageSize()

			return '', 200, {'Content-Type': 'text/plain'}


		@self.__ServerApp.route('/updatemmcords')
		def updatemmcords():
			self.MainMarkerCord = [int(request.args.get('x')), int(request.args.get('y'))]
			return '', 200, {'Content-Type': 'text/plain'}


		@self.__ServerApp.route('/autoaim')
		def autoaimstart():
			if self.ifAutoAimAvaliable:
				newMarkerCord = (int(request.args.get('x')), int(request.args.get('y')))
				controlFrame = self.Camera.getOneFrame()
				controlFrameSize = (controlFrame.shape[1], controlFrame.shape[0])

				nowMarkerCords = self.MainMarkerCord
				markerToMove1 = (newMarkerCord[0], self.MainMarkerCord[1])
				markerToMove2 = newMarkerCord

				marketToMoveField1, marketToMoveFieldVector1 = self.CheckerForAutoAim.changeNewMarkerFieldSize(controlFrame, controlFrameSize, markerToMove1)
				marketToMoveField2, marketToMoveFieldVector2 = self.CheckerForAutoAim.changeNewMarkerFieldSize(controlFrame, controlFrameSize, markerToMove2)


				threading.Thread(
					target=self.moveForAutoAim, 
					args=(
						controlFrame, controlFrameSize, 
						nowMarkerCords, markerToMove1, markerToMove2,
						marketToMoveField1, marketToMoveField2,
						marketToMoveFieldVector1, marketToMoveFieldVector2
					)).start()

			return '', 200, {'Content-Type': 'text/plain'}


		@self.__ServerApp.route('/gunmove')
		def gunmove():
			eventType = request.args.get('type')
			buttonID = request.args.get('id')

			if eventType == 'grided':
				self.gunsButtonStatus[buttonID] = True
				# self.Connector.send('{"command":"movegun_' + buttonID + '_start"}')

			elif eventType == 'buttonup':
				if not self.gunsButtonStatus[buttonID]: pass
					# self.Connector.send('{"command":"onemovegun_' + buttonID + '"}')
				else:
					self.gunsButtonStatus[buttonID] = False
					# self.Connector.send('{"command":"movegun_' + buttonID + '_stop"}')

			return '', 200, {'Content-Type': 'text/plain'}


		self.__ServerApp.run(
				debug=False, 
				host=self.configs['SERVER']['ip'], 
				port=int(self.configs['SERVER']['port'])
			)