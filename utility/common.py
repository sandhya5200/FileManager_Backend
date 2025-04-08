from fastapi import HTTPException
import cv2
import io

def capture_image():
    cam = cv2.VideoCapture(0)  #starting of the camera 0 defines the default number of camera 
    if not cam.isOpened():
        raise HTTPException(status_code=500, detail="Failed to open the camera")

    while True:  #this is an infinite loop where it takes continuous images 
        ret, frame = cam.read()  #frame contains image data and ret indicates if the frame is succesfully captured 
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to capture image")
        cv2.imshow("Camera - Press 'c' to capture, 'q' to quit", frame)  #this is to show on the camera display
        key = cv2.waitKey(1)   #it check every 1 millisecond for key press 

        if key == ord('c'):    #captures the current frame of the image ,ord is used to convert the single char to its unicode code point

            success, buffer = cv2.imencode('.jpg', frame)   #converts the captured frame into jpeg format and stores it in memory

            if not success:
                raise HTTPException(status_code=500, detail = "Failed to encode image") 
            
            cv2.destroyAllWindows()   
            return io.BytesIO(buffer).getvalue()   #returns the image as byte stream 
        
        elif key == ord('q'):
            cam.release()  #stops the camera 
            cv2.destroyAllWindows()   #closes the camera window
            raise HTTPException(status_code=400, detail="Image capture aborted by user")

