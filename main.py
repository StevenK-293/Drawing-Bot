import cv2
import numpy as np
import pyautogui
import time
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import keyboard
from pynput.mouse import Listener

cancel_drawing = False
DRAW_DELAY = 0.01

selected_image_path = None
canvas_top_left = None
canvas_bottom_right = None

# --- Utility function to capture a click ---
def capture_click():
    pos = None
    def on_click(x, y, button, pressed):
        nonlocal pos
        if pressed:
            pos = (x, y)
            return False
    with Listener(on_click=on_click) as listener:
        listener.join()
    return pos

# --- Image Processing Functions ---
def preprocess_image(image_path, threshold=150):
    """
    Convert the image to grayscale and apply a binary threshold.
    """
    img = Image.open(image_path).convert("L")
    img = img.point(lambda p: 255 if p > threshold else 0)
    return np.array(img)

def scale_contours(contours, img_shape, canvas_top_left, canvas_size):
    """
    Scale detected contours from the image's coordinate system
    to the canvas (drawing area) coordinate system.
    """
    scaled_contours = []
    img_height, img_width = img_shape
    canvas_width, canvas_height = canvas_size

    for contour in contours:
        contour = contour.reshape(-1, 2)
        scaled = []
        for (x, y) in contour:
            scaled_x = canvas_top_left[0] + (x / img_width) * canvas_width
            scaled_y = canvas_top_left[1] + (y / img_height) * canvas_height
            scaled.append((scaled_x, scaled_y))
        scaled_contours.append(np.array(scaled))
    return scaled_contours

# --- Drawing Function ---
def draw_contours(contours):
    global cancel_drawing
    pyautogui.PAUSE = DRAW_DELAY

    time.sleep(5)  
    for contour in contours:
        if cancel_drawing:
            break
        if len(contour) < 2:
            continue
        start_x, start_y = contour[0]
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        for point in contour[1:]:
            if cancel_drawing or keyboard.is_pressed('esc'):
                cancel_drawing = True
                break
            x, y = point
            pyautogui.moveTo(x, y)
        pyautogui.mouseUp()

    if cancel_drawing:
        messagebox.showinfo("Cancelled", "Drawing was cancelled!")
    else:
        messagebox.showinfo("Done", "Drawing complete!")

# --- Start Drawing ---
def start_drawing():
    global cancel_drawing, DRAW_DELAY
    cancel_drawing = False

    if selected_image_path is None:
        messagebox.showerror("Error", "No image selected!")
        return
    if canvas_top_left is None or canvas_bottom_right is None:
        messagebox.showerror("Error", "Canvas coordinates are not set!")
        return

    canvas_size = (canvas_bottom_right[0] - canvas_top_left[0],
                   canvas_bottom_right[1] - canvas_top_left[1])
    
    threshold_value = threshold_scale.get()
    processed_img = preprocess_image(selected_image_path, threshold=threshold_value)
    edges = cv2.Canny(processed_img, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    scaled_contours = scale_contours(contours, edges.shape, canvas_top_left, canvas_size)

    drawing_thread = threading.Thread(target=draw_contours, args=(scaled_contours,))
    drawing_thread.start()

# --- Preview Processed Image ---
def preview_processed_image():
    if not selected_image_path:
        messagebox.showerror("Error", "No image selected!")
        return
    threshold_value = threshold_scale.get()
    processed_img = preprocess_image(selected_image_path, threshold=threshold_value)
    edges = cv2.Canny(processed_img, 50, 150)
    img_pil = Image.fromarray(edges)
    img_tk = ImageTk.PhotoImage(img_pil)
    
    preview_window = tk.Toplevel(root)
    preview_window.title("Processed Image Preview")
    label = tk.Label(preview_window, image=img_tk)
    label.image = img_tk
    label.pack()

# --- GUI Functions ---
def select_image():
    global selected_image_path
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    if file_path:
        selected_image_path = file_path
        image_label.config(text=file_path)

def set_top_left():
    global canvas_top_left
    messagebox.showinfo("Set Top Left", "After clicking OK, click on the TOP-LEFT corner of the drawing canvas.")
    root.withdraw()
    pos = capture_click()
    root.deiconify()
    if pos:
        canvas_top_left = pos
        top_left_label.config(text=f"Top Left: {canvas_top_left}")
    else:
        messagebox.showerror("Error", "Failed to capture the top left coordinate.")

def set_bottom_right():
    global canvas_bottom_right
    messagebox.showinfo("Set Bottom Right", "After clicking OK, click on the BOTTOM-RIGHT corner of the drawing canvas.")
    root.withdraw()
    pos = capture_click()
    root.deiconify()
    if pos:
        canvas_bottom_right = pos
        bottom_right_label.config(text=f"Bottom Right: {canvas_bottom_right}")
    else:
        messagebox.showerror("Error", "Failed to capture the bottom right coordinate.")

def update_speed():
    global DRAW_DELAY
    speed = speed_var.get()
    if speed == "Slow":
        DRAW_DELAY = 0.05
    elif speed == "Normal":
        DRAW_DELAY = 0.01
    elif speed == "Fast":
        DRAW_DELAY = 0.001

# --- GUI Window ---
root = tk.Tk()
root.title("Drawing Bot")

# Row 0: Image selection
tk.Button(root, text="Select Image", command=select_image).grid(row=0, column=0, padx=10, pady=10)
image_label = tk.Label(root, text="No image selected")
image_label.grid(row=0, column=1, padx=10, pady=10)

# Row 1: Set Top Left coordinate
tk.Button(root, text="Set Top Left", command=set_top_left).grid(row=1, column=0, padx=10, pady=10)
top_left_label = tk.Label(root, text="Top Left: Not set")
top_left_label.grid(row=1, column=1, padx=10, pady=10)

# Row 2: Set Bottom Right coordinate
tk.Button(root, text="Set Bottom Right", command=set_bottom_right).grid(row=2, column=0, padx=10, pady=10)
bottom_right_label = tk.Label(root, text="Bottom Right: Not set")
bottom_right_label.grid(row=2, column=1, padx=10, pady=10)

# Row 3: Drawing speed selection
speed_var = tk.StringVar(value="Normal")
tk.Label(root, text="Drawing Speed:").grid(row=3, column=0, padx=10, pady=10)
speed_frame = tk.Frame(root)
speed_frame.grid(row=3, column=1, padx=10, pady=10)
tk.Radiobutton(speed_frame, text="Slow", variable=speed_var, value="Slow", command=update_speed).pack(side=tk.LEFT)
tk.Radiobutton(speed_frame, text="Normal", variable=speed_var, value="Normal", command=update_speed).pack(side=tk.LEFT)
tk.Radiobutton(speed_frame, text="Fast", variable=speed_var, value="Fast", command=update_speed).pack(side=tk.LEFT)

# Row 4: Threshold slider for image processing
tk.Label(root, text="Threshold:").grid(row=4, column=0, padx=10, pady=10)
threshold_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL)
threshold_scale.set(150)
threshold_scale.grid(row=4, column=1, padx=10, pady=10)

# Row 5: Preview processed image button
tk.Button(root, text="Preview Processed Image", command=preview_processed_image).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Row 6: Start drawing button
tk.Button(root, text="Start Drawing", command=start_drawing).grid(row=6, column=0, columnspan=2, padx=10, pady=20)

root.mainloop()
