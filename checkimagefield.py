import cv2
import numpy as np
import time
import threading



class AimMarkerCheck:
	printLogs = False


	def getKeyPoints(self, image, diviveK=1):
		if self.printLogs: print(f"Getting keypoints with step {diviveK}...")
		listToReturn = []
		keyPoints = cv2.SIFT_create().detectAndCompute(image, None)[0]

		if diviveK > 1: keyPoints = keyPoints[::diviveK]
		for point in keyPoints: listToReturn.append((round(point.pt[0]), round(point.pt[1])))

		if self.printLogs: print(f"Getted points: {len(listToReturn)}")
		return listToReturn

	def getImageSize(self, image): return (image.shape[1], image.shape[0])


	def changeNewMarkerFieldSize(self, image, imageSize, markerCords, markerFieldSize=None, startPos=(None, None), endPos=(None, None)):
		if self.printLogs: print(f"Setting field with marker cords {markerCords}...")

		if not markerFieldSize:
			markerFieldSize = [imageSize[0] * 0.25, imageSize[1] * 0.25]
			markerFieldSize = list(map(round, markerFieldSize))


		if startPos == (None, None) or endPos == (None, None):
			startPos = [markerCords[0] - markerFieldSize[0], markerCords[1] - markerFieldSize[1]]
			endPos = [markerCords[0] + markerFieldSize[0], markerCords[1] + markerFieldSize[1]]


		if startPos[0] < 0: startPos[0] = 0
		if startPos[1] < 0: startPos[1] = 0

		if endPos[0] > imageSize[0]: endPos[0] = imageSize[0]
		if endPos[1] > imageSize[1]: endPos[1] = imageSize[1]


		if self.printLogs: print(f"Field size: {markerFieldSize}")

		startPos = list(map(int, startPos))
		endPos = list(map(int, endPos))

		if self.printLogs: print(f"[FROMDOT] X: {startPos[0]}; Y: {startPos[1]};")
		if self.printLogs: print(f"[TODOT] X: {endPos[0]}; Y: {endPos[1]};")

		return image[
					startPos[1]:endPos[1],
					startPos[0]:endPos[0]
				], 	(
						markerCords[0] - startPos[0],
						markerCords[1] - startPos[1],
						endPos[0] - markerCords[0],
						endPos[1] - markerCords[1]
					)


	def checkPoints(self, pointsCords1, pointsCords2, imageSize, markerFieldSize, allowableErrorK = 0.007):
		if len(pointsCords1) == 0 or len(pointsCords2) == 0: return 0

		allowableDiap = (round(imageSize[0] * allowableErrorK), round(imageSize[1] * allowableErrorK))
		correctPoints = 0

		for pointIndex in range(0, len(pointsCords1)):
			try:
				if ((
					 pointsCords1[pointIndex][0] >= (pointsCords2[pointIndex][0] - allowableDiap[0])
					) and (
					 pointsCords1[pointIndex][0] <= pointsCords2[pointIndex][0] + allowableDiap[0]
					)) and ((
					 pointsCords1[pointIndex][1] >= (pointsCords2[pointIndex][1] - allowableDiap[1])
					) and (
					 pointsCords1[pointIndex][1] <= pointsCords2[pointIndex][1] + allowableDiap[1]
					)): correctPoints += 1
			except Exception as error:
				if self.printLogs: print(f'Error in checking keypoints: {error}')

		try: return 1 / min([len(pointsCords1), len(pointsCords2)]) * correctPoints
		except ZeroDivisionError: return 0


	def check(self, image, imageSize, marker1Cords, marker2Cords, marker1Field=None, marker2Field=None, ifTest=False):
		if self.printLogs: print("Creating fileds...")

		if not marker1Field: 
			marker1Field, marker1FieldSize = self.changeNewMarkerFieldSize(image, imageSize, marker1Cords)[:2]
		else: marker1FieldSize = (marker1Field.shape[1], marker1Field.shape[0])

		if not marker2Field: marker2Field, marker2FieldSize = self.changeNewMarkerFieldSize(image, imageSize, marker2Cords, markerFieldSize=marker1FieldSize)[:2]

		def showTestingImages():
			cv2.imshow("image", image)
			cv2.imshow("marker1Field", marker1Field)
			cv2.imshow("marker2Field", marker2Field)

			while True:
				time.sleep(1)

				if cv2.waitKey(1) & 0xFF == ord('q'):
					cv2.destroyAllWindows()
					break

		if self.printLogs: print("Getting keypoints...")
		pointsFromMarker1 = self.getKeyPoints(marker1Field)
		pointsFromMarker2 = self.getKeyPoints(marker2Field)

		if self.printLogs: print("Checking...")
		if ifTest: threading.Thread(target=showTestingImages).start()
		return self.checkPoints(pointsFromMarker1, pointsFromMarker2, imageSize, marker1FieldSize)



def analyzeImage(Checker, image, marker1cords, marker2cords, lastField1=None): # marker1cords - newMarker, marker2cords - lastMarker
	image = np.array(image)
	imgSize = (image.shape[1], image.shape[0])

	return Checker.check(image, imgSize, marker1cords, marker2cords, marker1Field=lastField1)


def main():
	checker = AimMarkerCheck()
	capture = cv2.VideoCapture(0)
	res, img = capture.read()

	if res:
		marker1Cords = (440, 400)
		marker2Cords = (420, 410)

		print(f"Result is: {analyzeImage(checker, img, marker1Cords, marker2Cords)}")


if __name__ == '__main__': main()