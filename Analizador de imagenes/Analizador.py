import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
from pathlib import Path
from tkinter import ttk

class ImageFilterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Analizador y Buscador de Colores")
        self.master.configure(bg="#F0F0F0")

        self.deferred_update_id = None

        self.original_images = []
        self.processed_images = []
        self.image_paths = []

        self.scaled_images = []

        self.current_index = 0
        self.zoom_factor = 1.0
        self.processing_enabled = False

        self.scan_start_x = 0
        self.scan_start_y = 0

        self.total_images_in_folder = 0  

        self.zoom_var = tk.DoubleVar()
        self.zoom_var.set(1.0) 
        self.zoom_var.trace_add("write", self.update_zoom)

        self.h_var = tk.DoubleVar()
        self.s_var = tk.DoubleVar()
        self.v_var = tk.DoubleVar()

        self.lower_bound_adjust = [100, 50, 50]
        self.upper_bound_adjust = [130, 255, 100]

        self.create_toolbar()
        self.create_zoom_frame()
        self.create_image_canvas()

    def create_toolbar(self):
        self.toolbar = tk.Frame(self.master, relief=tk.RAISED, bd=2, bg="#34495E")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        action_container = tk.Frame(self.toolbar)
        action_container.pack(side=tk.LEFT)

        self.create_action_group()  

        navigation_container = tk.Frame(self.toolbar)
        navigation_container.pack(side=tk.LEFT, padx=10)

        self.create_navigation_group(navigation_container)

        self.create_hsv_group()
        self.create_save_exit_group()
        
    def create_action_group(self):
        action_group = ttk.LabelFrame(self.toolbar, text="Acciones Generales", labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        action_group.pack(side=tk.LEFT, padx=10)

        action_label = ttk.Label(action_group, text="Realice una acción:", foreground="#2C3E50", font=("Arial", 10, "bold"))
        action_label.pack()

        self.load_button = tk.Button(action_group, text="Cargar Imagen", command=self.load_image, bg="#3498db", fg="white", font=("Arial", 8))
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))

        self.open_folder_button = tk.Button(action_group, text="Abrir Carpeta", command=self.open_folder, bg="#3498db", fg="white", font=("Arial", 8))
        self.open_folder_button.pack(side=tk.LEFT)

    def create_navigation_group(self, parent):
        navigation_group = ttk.LabelFrame(parent, text="Opciones de Navegación", labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        navigation_group.pack()

        navigation_label = ttk.Label(navigation_group, text="Seleccione una acción:", foreground="#2C3E50", font=("Arial", 10, "bold"))
        navigation_label.grid(row=0, column=0, columnspan=2)

        self.prev_button = tk.Button(navigation_group, text="Anterior", command=self.show_previous_image, bg="#3498db", fg="white", font=("Arial", 8))
        self.prev_button.grid(row=1, column=0, pady=(0, 5))

        self.next_button = tk.Button(navigation_group, text="Siguiente", command=self.show_next_image, bg="#3498db", fg="white", font=("Arial", 8))
        self.next_button.grid(row=1, column=1, pady=(0, 5))

    def create_hsv_group(self):
        hsv_group = ttk.LabelFrame(self.toolbar, text="Ajustes de Color (HSV)", labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        hsv_group.pack(side=tk.LEFT, padx=10)

        style = ttk.Style()

        sliders = [("Hue", 0, 179, self.h_var), ("Saturation", 0, 255, self.s_var), ("Value", 0, 255, self.v_var)]

        for label, min_val, max_val, var in sliders:
            slider_frame = ttk.Frame(hsv_group)
            slider_frame.pack(side=tk.LEFT, padx=10)

            slider = tk.Scale(slider_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var, command=self.update_filter, length=147)
            slider.pack(side=tk.LEFT)

            entry = tk.Entry(slider_frame, textvariable=var, width=5, font=("Arial", 8))
            entry.pack(side=tk.LEFT)
            entry.bind("<FocusOut>", self.update_slider_from_entry)

        self.toggle_filter_button = tk.Button(hsv_group, text="Activar Filtro", command=self.toggle_processing, bg="#3498db", fg="white", font=("Arial", 8))
        self.toggle_filter_button.pack(side=tk.LEFT, padx=10)

    def create_zoom_frame(self):
        self.zoom_frame = ttk.Frame(self.master, style='Custom.TLabelframe')
        self.zoom_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.create_zoom_group()
        self.create_position_group(self.zoom_frame) 

    def create_zoom_group(self):
        zoom_group = ttk.LabelFrame(self.zoom_frame, text="Zoom y Navegación",labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        zoom_group.pack(side=tk.LEFT, padx=10)

        zoom_label = ttk.Label(zoom_group, text="Datos de la imagen seleccionada:", foreground="#2C3E50", font=("Arial", 10, "bold"))
        zoom_label.pack(side=tk.TOP, pady=(0, 10))

        self.zoom_slider = tk.Scale(zoom_group, from_=0.1, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.zoom_var, command=self.update_zoom, length=200)
        self.zoom_slider.pack(side=tk.LEFT, padx=(0, 10))

        self.zoom_value_label = ttk.Label(zoom_group, text="Zoom:", foreground="#333333", font=("Arial", 8))
        self.zoom_value_label.pack(side=tk.LEFT)

        self.zoom_entry = tk.Entry(zoom_group, textvariable=self.zoom_var, width=5, font=("Arial", 8))
        self.zoom_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.zoom_entry.bind("<FocusOut>", self.update_slider_from_entry)
        self.zoom_entry.bind("<Return>", self.update_zoom)

        self.image_name_label = ttk.Label(zoom_group, text="Imagen Actual: ", foreground="#333333", font=("Arial", 8))
        self.image_name_label.pack(side=tk.RIGHT)
        

    def create_image_canvas(self):
        self.image_canvas = tk.Canvas(self.master, bg="#FFFFFF", width=500, height=500)
        self.image_canvas.pack()

        self.image_canvas.bind("<Configure>", self.adjust_canvas_view)

        self.image_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  

    def create_save_exit_group(self):
        save_exit_group = ttk.LabelFrame(self.toolbar, text="Guardar Imagen y Salir", labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        save_exit_group.pack(side=tk.RIGHT, padx=10)

        save_exit_label = ttk.Label(save_exit_group, text="Seleccione una opción:", foreground="#2C3E50", font=("Arial", 10, "bold"))
        save_exit_label.grid(row=0, column=0, columnspan=2, pady=(0, 5)) 

        self.save_button = tk.Button(save_exit_group, text="Guardar", command=self.save_image, bg="#3498db", fg="white", font=("Arial", 8))
        self.save_button.grid(row=1, column=0, padx=5)  

        self.exit_button = tk.Button(save_exit_group, text="Salir", command=self.exit_application, bg="#3498db", fg="white", font=("Arial", 8))
        self.exit_button.grid(row=1, column=1, padx=5)  

    def create_position_group(self, parent):
        position_group = ttk.LabelFrame(parent, text="Posición de la Imagen", labelanchor="n", style='Custom.TLabelframe', padding=(10, 5))
        position_group.pack(side=tk.LEFT, padx=10)

        position_label = ttk.Label(position_group, text="Esta en la imagen:", foreground="#2C3E50", font=("Arial", 10, "bold"))
        position_label.pack()

        self.position_label = ttk.Label(position_group, text="", foreground="#333333")
        self.position_label.pack()

    def center_window(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = self.master.winfo_reqwidth()
        window_height = self.master.winfo_reqheight()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def toggle_processing(self):
        if self.image_paths:
            self.processing_enabled = not self.processing_enabled
            self.update_toggle_button_text()
            self.process_image()
        else:
            messagebox.showwarning("Aviso", "Cargue una imagen antes de activar o desactivar el filtro.")

    def update_toggle_button_text(self):
        if self.processing_enabled:
            self.toggle_filter_button.config(text="Desactivar Filtro")
        else:
            self.toggle_filter_button.config(text="Activar Filtro")

    def apply_color_adjustments(self, image, hue, saturation, value):
        try:
            if not isinstance(image, np.ndarray):
                image = np.array(image)

            if len(image.shape) == 2:  
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 4:  
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            elif len(image.shape) == 3 and image.shape[2] != 3:  
                raise ValueError("La imagen debe estar en formato RGB o escala de grises (3 canales)")

            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

            lower_bound = np.array([hue, saturation, value]) - np.array(self.lower_bound_adjust)
            upper_bound = np.array([hue, saturation, value]) + np.array(self.upper_bound_adjust)

            mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

            result_image = 255 * np.ones_like(image)

            result_image[mask != 0] = image[mask != 0]

            return result_image
        except ValueError as ve:
            messagebox.showerror("Error", f"Error en el formato de la imagen: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar ajustes de color: {e}")

    def load_image(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
            if file_path:
                with Image.open(file_path) as image_file:
                    self.image_paths = [file_path]
                    self.current_index = 0
                    self.original_images = [np.array(image_file)]
                    self.scaled_images = [self.scale_image(Image.fromarray(self.original_images[0]), self.zoom_factor)]
                    self.processed_images = self.original_images.copy()
                    self.display_image(self.original_images[0])
                    self.process_image()
                    self.reset_image_counter()
                    self.adjust_canvas_view()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar la imagen: {e}")


    def open_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.image_paths = [os.path.join(folder_selected, file) for file in os.listdir(folder_selected) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.original_images = [cv2.cvtColor(cv2.imread(file), cv2.COLOR_BGR2RGB) for file in self.image_paths]
            self.scaled_images = [self.scale_image(img, self.zoom_factor) for img in self.original_images]
            self.processed_images = self.original_images.copy()
            self.current_index = 0
            self.total_images_in_folder = len(self.image_paths)
            self.process_image()
            self.reset_image_counter()
            if self.total_images_in_folder > 0:
                self.show_current_image()
                self.adjust_canvas_view()
            else:
                self.image_canvas.delete("all")

    def reset_image_counter(self):
        if self.image_paths:
            if len(self.image_paths) == 1: 
                counter_text = f"Imagen: 1/1"
            else:
                current_position = self.current_index + 1
                counter_text = f"Imagen {current_position}/{self.total_images_in_folder}" if self.total_images_in_folder > 0 else "Imágenes Cargadas: 1"
        else:
            counter_text = "No hay imágenes cargadas"

        self.position_label.config(text=counter_text)

    def show_previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
            self.reset_image_counter()

    def show_next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.show_current_image()
            self.reset_image_counter()

    def show_current_image(self):
        self.display_image(self.scaled_images[self.current_index])
        self.update_zoom()

    def update_zoom(self, *args):
        zoom_level = self.zoom_var.get()
        self.master.after(200, self.deferred_update_image, zoom_level)

    def deferred_update_image(self, zoom_level):
        if 0 <= self.current_index < len(self.original_images):
            image_to_display = self.processed_images[self.current_index] if self.processing_enabled else self.original_images[self.current_index]

            resized_image = self.scale_image(image_to_display, zoom_level)

            self.display_image(resized_image)


    def scale_image(self, image, scale_factor):
        if isinstance(image, np.ndarray):
            height, width, _ = image.shape
        else:
            width, height = image.size

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        if isinstance(image, np.ndarray):
            return cv2.resize(image, (new_width, new_height))
        else:
            return image.resize((new_width, new_height), Image.LANCZOS)


    def update_slider_from_entry(self, event):
        try:
            slider_value = float(self.zoom_var.get())
            self.zoom_slider.set(slider_value)
            self.update_zoom()
        except ValueError:
            pass
    
    def update_filter(self, *args):
        if self.image_paths:
            if 0 <= self.current_index < len(self.processed_images):
                hue = int(self.h_var.get())
                saturation = int(self.s_var.get())
                value = int(self.v_var.get())
                self.processed_images[self.current_index] = self.apply_color_adjustments(
                    self.original_images[self.current_index], hue, saturation, value)
                self.process_image()  
            else:
                messagebox.showwarning("Aviso", "No hay imágenes cargadas o el índice actual está fuera de rango.")
        else:
            messagebox.showwarning("Aviso", "Cargue una imagen antes de activar o desactivar el filtro.")

    def display_image(self, image):
        try:
            if not isinstance(image, np.ndarray):
                image = np.array(image)

            image = Image.fromarray(image)
            photo = ImageTk.PhotoImage(image)

            self.image_canvas.config(width=photo.width(), height=photo.height())
            self.image_canvas.create_image(0, 0, anchor="nw", image=photo)
            self.image_canvas.image = photo  

            image_name = f"Imagen Actual: {os.path.basename(self.image_paths[self.current_index])}"
            self.image_name_label.config(text=image_name)

        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar la imagen: {e}")

    def process_image(self):
        if self.processing_enabled and self.image_paths and 0 <= self.current_index < len(self.original_images):
            hue = int(self.h_var.get())
            saturation = int(self.s_var.get())
            value = int(self.v_var.get())
            
            try:
                self.processed_images[self.current_index] = self.apply_color_adjustments(
                    self.original_images[self.current_index], hue, saturation, value)
                self.display_image(self.processed_images[self.current_index])
            except Exception as e:
                messagebox.showerror("Error", f"Error al aplicar ajustes de color: {e}")
        elif self.image_paths and 0 <= self.current_index < len(self.original_images):
            self.display_image(self.original_images[self.current_index])
        else:
            messagebox.showwarning("Aviso", "No hay imágenes cargadas o el índice actual está fuera de rango.")

    def start_pan(self, event):
        self.image_canvas.scan_mark(event.x, event.y)

    def on_mouse_drag(self, event):
        self.image_canvas.scan_dragto(event.x, event.y, gain=1)

    def on_mouse_wheel(self, event):
        zoom_factor = 1.2 if event.delta > 0 else 0.8
        new_zoom = self.zoom_var.get() * zoom_factor

        new_zoom = max(0.1, min(3.0, new_zoom))

        self.zoom_var.set(new_zoom)
        self.update_zoom()

    def adjust_canvas_view(self, event=None):
        if self.image_paths:
            if 0 <= self.current_index < len(self.processed_images):
                current_image = self.processed_images[self.current_index] if self.processing_enabled else self.original_images[self.current_index]

                img_width, img_height = current_image.shape[1], current_image.shape[0]

                scaled_width = int(img_width * self.zoom_factor)
                scaled_height = int(img_height * self.zoom_factor)

                scaled_image = cv2.resize(current_image, (scaled_width, scaled_height))

                x_center = int(self.image_canvas.winfo_width() / 2)
                y_center = int(self.image_canvas.winfo_height() / 2)

                x_start = x_center - int(scaled_width / 2)
                y_start = y_center - int(scaled_height / 2)

                x_offset = x_start - self.scan_start_x
                y_offset = y_start - self.scan_start_y

                self.scan_start_x = x_start
                self.scan_start_y = y_start

                self.image_canvas.delete("all")

                self.image_canvas.create_image(x_center, y_center, anchor=tk.CENTER, image=self.image_canvas.image)

                self.scan_start_x = x_start
                self.scan_start_y = y_start
            else:
                messagebox.showwarning("Aviso", "El índice actual está fuera de rango.")
        else:
            messagebox.showwarning("Aviso", "No hay imágenes cargadas.")

    def run(self):
        self.master.mainloop()

    def exit_application(self):
        self.master.destroy()

    def save_image(self):
        if self.image_paths:
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if save_path:
                current_image = self.processed_images[self.current_index] if self.processing_enabled else self.original_images[self.current_index]
                cv2.imwrite(save_path, cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB))
                messagebox.showinfo("Guardado", "La imagen ha sido guardada exitosamente.")
        else:
            messagebox.showwarning("Aviso", "Cargue una imagen antes de intentar guardar.")

def main():
    root = tk.Tk()
    app = ImageFilterApp(root)
    app.run()

if __name__ == "__main__":
    main()