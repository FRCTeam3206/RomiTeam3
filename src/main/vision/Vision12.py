import cv2
 

known_distance = 30 
Known_Width = 6.35

block_dectector = cv2.CascadeClassifier()
cap = cv2.VideoCapture(1)

while True:
    _, frame = cap.read()

    cv2.imshow("frame",frame )
    if cv2.waitkey(1)==ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
