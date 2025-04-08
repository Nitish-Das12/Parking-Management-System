import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import numpy as np

# Car Detection using YOLO
class CarDetector:
    def __init__(self):  # Corrected the method name to __init__
        # Load YOLO pre-trained weights and configuration files
        self.net = cv2.dnn.readNetFromDarknet("C:/Users/acer/Downloads/yolov4.cfg", "C:/Users/acer/Downloads/yolov4.weights")
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

    def detect_cars(self, frame):
        # Prepare image for detection
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes = []
        confidences = []
        class_ids = []
        height, width, _ = frame.shape

        # Loop through detections
        for out in outputs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Only consider cars (class ID 2 corresponds to 'car' in YOLO)
                if confidence > 0.5 and class_id == 2:
                    # Get bounding box coordinates
                    x, y, w, h = map(int, detection[0:4] * [width, height, width, height])
                    x = int(x - w / 2)
                    y = int(y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply Non-Maximum Suppression (NMS) to filter out overlapping boxes
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        # Check if NMS returned valid indices
        if len(indices) > 0:
            indices = indices.flatten()  # Convert to 1D array
            boxes = [boxes[i] for i in indices]  # Filter boxes based on the indices
        return boxes


# Car Parking System with Parking Slot Management
class ParkingLot:
    def __init__(self, total_slots):  # Corrected the method name to __init__
        self.total_slots = total_slots
        self.available_slots = total_slots
        self.slots = [False] * total_slots  # List of boolean values representing whether the slot is occupied

    def park_car(self):
        for i in range(self.total_slots):
            if not self.slots[i]:  # If the slot is available
                self.slots[i] = True
                self.available_slots -= 1
                return i  # Return the index of the parked slot
        return -1  # No available slots

    def remove_car(self, slot_index):
        if self.slots[slot_index]:
            self.slots[slot_index] = False
            self.available_slots += 1
            return True
        return False

    def get_parking_status(self):
        return f"{self.available_slots}/{self.total_slots} slots available"

    def get_slot_status(self):
        # Return a list of slot statuses (occupied or free)
        return ['Occupied' if occupied else 'Free' for occupied in self.slots]


# GUI for Car Detection and Parking
class CarDetectionSystem:
    def __init__(self, root):  # Corrected the method name to __init__
        self.root = root
        self.root.title("Car Detection and Parking Management")
        self.root.geometry("600x600")
        self.root.configure(bg='#1E2A38')  # Dark background color
        
        self.car_detector = CarDetector()
        self.parking_lot = ParkingLot(total_slots=20)  # Changed from 10 to 20 slots
        
        # Frame for the UI elements
        self.frame = tk.Frame(self.root, bg='#1E2A38')
        self.frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Button to select video file
        self.detect_button = tk.Button(self.frame, text="Select Video File", font=("Arial", 14, 'bold'), bg='#007BFF', fg='white', command=self.select_video_file, relief='solid', bd=2)
        self.detect_button.pack(pady=10)

        # Display parking status
        self.parking_status_label = tk.Label(self.frame, text=self.parking_lot.get_parking_status(), font=("Arial", 16, "bold"), fg="#FF0000", bg="#1E2A38")
        self.parking_status_label.pack(pady=20)

        self.video_filepath = ""
        self.car_slot_mapping = {}  # Mapping from car bounding box to parking slots

    def select_video_file(self):
        # Open file dialog to select a video file
        self.video_filepath = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")])
        if self.video_filepath:
            self.start_video_processing()

    def start_video_processing(self):
        # Open the video file
        cap = cv2.VideoCapture(self.video_filepath)
        if not cap.isOpened():
            print("Error: Could not open video file.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect cars in the frame
            boxes = self.car_detector.detect_cars(frame)
            
            # Update parking slots based on detected cars
            self.update_parking_status(boxes)

            # Draw bounding boxes around detected cars
            for box in boxes:
                x, y, w, h = box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box for detected cars

            # Display parking status
            cv2.putText(frame, self.parking_lot.get_parking_status(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Show the frame
            cv2.imshow("Car Detection and Parking", frame)

            # Break on ESC key
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key to stop
                break

        cap.release()
        cv2.destroyAllWindows()

    def update_parking_status(self, boxes):
        detected_cars = []

        # Loop through the detected cars and park them
        for box in boxes:
            detected_cars.append(tuple(box))  # Convert to tuple for consistency

        # Check if any cars need to be parked
        for car in detected_cars:
            if car not in self.car_slot_mapping:  # If the car is not already parked
                slot_index = self.parking_lot.park_car()
                if slot_index != -1:
                    self.car_slot_mapping[car] = slot_index  # Map the car to a parking slot
                    print(f"Car detected, parking in Slot {slot_index + 1}. {self.parking_lot.get_parking_status()}")

        # Check for cars that have left
        parked_cars = list(self.car_slot_mapping.keys())
        for parked_car in parked_cars:
            if parked_car not in detected_cars:  # If the car is no longer detected
                slot_index = self.car_slot_mapping.pop(parked_car)
                self.parking_lot.remove_car(slot_index)
                print(f"Car left, freeing Slot {slot_index + 1}. {self.parking_lot.get_parking_status()}")

# Start the application
if __name__ == "__main__":  # Fixed the if statement
    root = tk.Tk()
    app = CarDetectionSystem(root)
    root.mainloop()
