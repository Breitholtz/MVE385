# way to get a point on the screen and draw around it takes an image as an argument with flag --image


# import packages

import argparse
import cv2
import numpy as np
refPt=[]
chosen=False
test_points= [ (125,100), (500,500),(25,25)]
def compare_points(image,points,chosen_point):
	# takes a list points and checks which of them is closest to chosen_point
	dist=[]
	for i in range(len(points)):
		dist.append((points[i][0]-chosen_point[0][0])**2+(points[i][1]-chosen_point[0][1])**2)
	print("Distances calculated:")
	print(dist)
	# choose the point closest and translate the image
	# this so that the image will line up with the one it is compared to 
	a=[x for _,x in sorted(zip(dist,points))]
	delta_x=a[0][0]
	delta_y=a[0][1]
	num_rows, num_cols = image.shape[:2]
	translation_matrix = np.float32([ [1,0,delta_x], [0,1,delta_y] ])
	image_translation = cv2.warpAffine(image, translation_matrix, (num_cols, num_rows))
	cv2.imshow('Translation', image_translation)


# count empty space to give a metric if any image needs to be redone
def choose_midpoint(event,x,y,flags, param):
	global refPt, chosen, test_points

# if we click the mouse we draw a circle around where we click
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt=[(x,y)]
		chosen = True
	elif event== cv2.EVENT_LBUTTONUP:
		refPt.append((x,y))
		chosen=False

		compare_points(image,test_points,refPt)
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
