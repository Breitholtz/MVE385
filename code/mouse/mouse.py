# way to get a point on the screen and draw around it takes an image as an argument with flag --image


# import packages

import argparse
import cv2
import numpy as np
refPt=[]
first_point=[]
chosen=False
test_points= [ (125,100), (500,500),(25,25)]
def compare_points(image,points,chosen_point):
	# takes a list points and checks which of them is closest to chosen_point
	dist=[]
	for i in range(len(points)):
		dist.append((points[i][0]-chosen_point[0][0])**2+(points[i][1]-chosen_point[0][1])**2)
	print("Distances calculated:")
	print(dist)
	print("Point that was chosen in previous picture:")
	print(points)
	# choose the point closest and translate the image
	# this so that the image will line up with the one it is compared to 
	a=[x for _,x in sorted(zip(dist,points))]
	delta_x=np.abs(a[0][0]-chosen_point[0][0])
	delta_y=np.abs(a[0][1]-chosen_point[0][1])
	print("delta x")
	print(delta_x)
	print("delta y")
	print(delta_y)
	num_rows, num_cols = image.shape[:2]
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	translation_matrix = np.float32([ [1,0,delta_x], [0,1,delta_y] ])
	image_translation = cv2.warpAffine(image, translation_matrix, (num_cols, num_rows))
	cv2.imshow('Translation', image_translation)
	gray_after = cv2.cvtColor(image_translation,cv2.COLOR_BGR2GRAY)

	# count empty space to give a metric if any image needs to be redone
	print("--------")
	num_pixels=num_rows*num_cols
	num_black_before=cv2.countNonZero(gray)
	num_black_after=cv2.countNonZero(gray_after)
	print("Percent of image that is black:")
	print((num_black_before-num_black_after)/num_pixels*100)
	print("--------")



def choose_second_point(event,x,y,flags, param):
	global refPt, chosen, test_points

# if we click the mouse we draw a circle around where we click
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt=[(x,y)]
		chosen = True
	elif event== cv2.EVENT_LBUTTONUP:
		chosen=False

		compare_points(image2,first_point,refPt)
		cv2.circle(image2, refPt[0],3,(255,255,255),1)
		cv2.imshow("image",image2)


def choose_first_point(event,x,y,flags,param):
	global refPt, chosen, first_point

# if we click the mouse we draw a circle around where we click
	if event == cv2.EVENT_LBUTTONDOWN:
		first_point=[(x,y)]
		chosen = True
	elif event== cv2.EVENT_LBUTTONUP:
		chosen=False
		print(first_point)
		cv2.circle(image, first_point[0],3,(255,255,255),1)
		cv2.imshow("image",image)


def output_data():
	global refPt, first_point 
# initialise argument parser

ap=argparse.ArgumentParser()
ap.add_argument("-i1","--im1",required=True, help="path to the first image you want to use")
ap.add_argument("-i2","--im2",required=True,help="path to the second image you want to use")
args=vars(ap.parse_args())

# load chosen first image and setup mouse callback function

image = cv2.imread(args["im1"])
clone=image.copy()
cv2.namedWindow("image1")
cv2.setMouseCallback("image1",choose_first_point)

# loop for first image and wait for keypress


while True:
	cv2.imshow("image1",image)
	key=cv2.waitKey(1) & 0xFF

	# if r is pressed reset the point
	if key == ord("r"):
	 image= clone.copy()
	# if c is pressed break from loop
	if key == ord("c"):
	 break

cv2.destroyAllWindows()
# load chosen second image and setup mouse callback function

image2 = cv2.imread(args["im2"])
clone=image.copy()
cv2.namedWindow("image2")
cv2.setMouseCallback("image2",choose_second_point)
# loop for second image and wait for keypress
while True:
	cv2.imshow("image2",image2)
	key=cv2.waitKey(1) & 0xFF

	# if r is pressed reset the point
	if key == ord("r"):
	 image= clone.copy()

	# if c is pressed break from loop
	if key == ord("c"):
	 output_data()
	 break


cv2.destroyAllWindows()
