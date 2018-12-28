# way to get a point on the screen and draw around it takes an image as an argument with flag --image


# import packages

import argparse
import cv2

refPt=[]
chosen=False

def choose_midpoint(event,x,y,flags, param):
	global refPt, chosen

# if we click the mouse we draw a circle around where we click
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt=[(x,y)]
		chosen = True
	elif event== cv2.EVENT_LBUTTONUP:
		refPt.append((x,y))
		chosen=False

		cv2.circle(image, refPt[0],3,(255,255,255),1)
		cv2.imshow("image",image)

# initialise argument parser

ap=argparse.ArgumentParser()
ap.add_argument("-i","--image",required=True, help="path to the image you want to use")
args=vars(ap.parse_args())

# load chosen image and setup mouse callback function

image = cv2.imread(args["image"])
clone=image.copy()
cv2.namedWindow("image")
cv2.setMouseCallback("image",choose_midpoint)

# loop and wait for keypress
while True:
	cv2.imshow("image",image)
	key=cv2.waitKey(1) & 0xFF

	# if r is pressed reset the point
	if key == ord("r"):
	 image= clone.copy()

	# if c is pressed break from loop
	if key == ord("c"):
	 break

cv2.destroyAllWindows()
