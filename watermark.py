#!/usr/bin/env python3
"""
Visual Watermark Remover Tool
This tool lets you manually select watermark areas to remove from videos
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading

class VisualWatermarkRemover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Visual Watermark Remover")
        self.root.geometry("1000x700")
        
        self.video_path = None
        self.frame = None
        self.original_frame = None
        self.removal_areas = []
        self.current_selection = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(file_frame, text="📁 Select Video", command=self.select_video).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(file_frame, text="No video selected")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Canvas for video preview
        self.canvas = tk.Canvas(main_frame, width=600, height=400, bg='black')
        self.canvas.grid(row=1, column=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # Control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.N, tk.W))
        
        ttk.Label(control_frame, text="🎯 Watermark Removal", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Platform presets
        ttk.Label(control_frame, text="Quick Presets:").pack(pady=5)
        preset_frame = ttk.Frame(control_frame)
        preset_frame.pack(pady=5)
        
        ttk.Button(preset_frame, text="TikTok", command=lambda: self.apply_preset("tiktok")).pack(pady=2, fill=tk.X)
        ttk.Button(preset_frame, text="Instagram", command=lambda: self.apply_preset("instagram")).pack(pady=2, fill=tk.X)
        ttk.Button(preset_frame, text="Snapchat", command=lambda: self.apply_preset("snapchat")).pack(pady=2, fill=tk.X)
        
        # Manual selection
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(control_frame, text="Manual Selection:").pack(pady=5)
        ttk.Label(control_frame, text="1. Click and drag on video\n2. to select watermark area").pack(pady=5)
        
        # Removal areas list
        ttk.Label(control_frame, text="Selected Areas:").pack(pady=5)
        self.areas_listbox = tk.Listbox(control_frame, height=4, width=25)
        self.areas_listbox.pack(pady=5)
        
        ttk.Button(control_frame, text="🗑️ Clear All", command=self.clear_areas).pack(pady=2)
        
        # Processing options
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(control_frame, text="Processing:").pack(pady=5)
        
        self.crop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Crop borders", variable=self.crop_var).pack(pady=2)
        
        self.enhance_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Enhance quality", variable=self.enhance_var).pack(pady=2)
        
        # Process button
        ttk.Button(control_frame, text="🚀 Remove Watermarks", 
                  command=self.process_video, style='Accent.TButton').pack(pady=10, fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready - Select a video to start")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
    def select_video(self):
        """Select video file"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"),
            ("All files", "*.*")
        ]
        
        self.video_path = filedialog.askopenfilename(filetypes=filetypes)
        
        if self.video_path:
            self.file_label.config(text=os.path.basename(self.video_path))
            self.load_video_frame()
            self.status_label.config(text=f"Video loaded: {os.path.basename(self.video_path)}")
    
    def load_video_frame(self):
        """Load first frame of video for preview"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Resize frame to fit canvas
                height, width = frame.shape[:2]
                canvas_width, canvas_height = 600, 400
                
                # Calculate scaling to fit canvas while maintaining aspect ratio
                scale = min(canvas_width/width, canvas_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                frame = cv2.resize(frame, (new_width, new_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                self.original_frame = frame.copy()
                self.frame = frame.copy()
                self.display_frame()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not load video: {e}")
    
    def display_frame(self):
        """Display frame on canvas"""
        if self.frame is not None:
            # Convert to PIL Image
            image = Image.fromarray(self.frame)
            photo = ImageTk.PhotoImage(image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(300, 200, image=photo)
            self.canvas.image = photo  # Keep a reference
            
            # Draw removal areas
            for i, (x1, y1, x2, y2) in enumerate(self.removal_areas):
                self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
                self.canvas.create_text(x1+5, y1+5, text=f"Area {i+1}", fill='red', anchor='nw')
    
    def start_selection(self, event):
        """Start selecting watermark area"""
        self.current_selection = [event.x, event.y, event.x, event.y]
    
    def update_selection(self, event):
        """Update selection rectangle"""
        if self.current_selection:
            self.current_selection[2] = event.x
            self.current_selection[3] = event.y
            
            # Redraw frame with current selection
            self.display_frame()
            x1, y1, x2, y2 = self.current_selection
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='yellow', width=2)
    
    def end_selection(self, event):
        """End selection and add to removal areas"""
        if self.current_selection:
            x1, y1, x2, y2 = self.current_selection
            
            # Make sure coordinates are in correct order
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            # Only add if selection is big enough
            if abs(x2-x1) > 10 and abs(y2-y1) > 10:
                self.removal_areas.append((x1, y1, x2, y2))
                self.areas_listbox.insert(tk.END, f"Area {len(self.removal_areas)}: {x2-x1}x{y2-y1}")
                self.display_frame()
            
            self.current_selection = None
    
    def apply_preset(self, platform):
        """Apply platform-specific preset watermark areas"""
        self.clear_areas()
        
        if not self.frame is None:
            h, w = self.frame.shape[:2]
            
            if platform == "tiktok":
                # TikTok watermark areas
                self.removal_areas = [
                    (w-180, h-100, w-10, h-10),  # Bottom-right logo
                    (10, h-80, 200, h-10),       # Bottom-left username
                ]
            elif platform == "instagram":
                # Instagram watermark areas
                self.removal_areas = [
                    (10, 10, 250, 60),           # Top-left username
                    (w-100, h-50, w-10, h-10),   # Bottom-right
                ]
            elif platform == "snapchat":
                # Snapchat watermark areas
                self.removal_areas = [
                    (10, h-100, 200, h-10),      # Bottom-left
                    (w-150, h-60, w-10, h-10),   # Bottom-right
                ]
            
            # Update listbox
            for i, (x1, y1, x2, y2) in enumerate(self.removal_areas):
                self.areas_listbox.insert(tk.END, f"Area {i+1}: {x2-x1}x{y2-y1}")
            
            self.display_frame()
            self.status_label.config(text=f"{platform.title()} preset applied")
    
    def clear_areas(self):
        """Clear all removal areas"""
        self.removal_areas = []
        self.areas_listbox.delete(0, tk.END)
        if self.frame is not None:
            self.display_frame()
    
    def process_video(self):
        """Process video to remove watermarks"""
        if not self.video_path:
            messagebox.showwarning("Warning", "Please select a video first")
            return
        
        if not self.removal_areas and not (self.crop_var.get() or self.enhance_var.get()):
            messagebox.showwarning("Warning", "Please select watermark areas or enable processing options")
            return
        
        # Check FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showerror("Error", "FFmpeg not found! Please install FFmpeg first.")
            return
        
        # Start processing in separate thread
        self.progress.start()
        self.status_label.config(text="Processing video...")
        
        thread = threading.Thread(target=self._process_video_thread)
        thread.daemon = True
        thread.start()
    
    def _process_video_thread(self):
        """Process video in separate thread"""
        try:
            # Get video dimensions
            cap = cv2.VideoCapture(self.video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Calculate scaling factor from canvas to video
            canvas_width, canvas_height = 600, 400
            scale_x = width / canvas_width
            scale_y = height / canvas_height
            
            # Convert removal areas to video coordinates
            video_areas = []
            for x1, y1, x2, y2 in self.removal_areas:
                vx1 = int(x1 * scale_x)
                vy1 = int(y1 * scale_y)
                vx2 = int(x2 * scale_x)
                vy2 = int(y2 * scale_y)
                video_areas.append((vx1, vy1, vx2-vx1, vy2-vy1))  # x, y, width, height
            
            # Build FFmpeg filter
            filters = []
            
            # Add delogo filters for each area
            for x, y, w, h in video_areas:
                filters.append(f"delogo=x={x}:y={y}:w={w}:h={h}:show=0")
            
            # Add crop if enabled
            if self.crop_var.get():
                filters.append("crop=iw-40:ih-60:20:30")
            
            # Add enhancement if enabled
            if self.enhance_var.get():
                filters.append("unsharp=5:5:1.0:5:5:0.0")
            
            # Create output filename
            base_name = os.path.splitext(self.video_path)[0]
            output_path = f"{base_name}_no_watermark.mp4"
            
            # Build and run FFmpeg command
            filter_string = ",".join(filters) if filters else "copy"
            
            cmd = [
                'ffmpeg', '-i', self.video_path,
                '-vf', filter_string,
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                '-c:a', 'copy', '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Update UI in main thread
            self.root.after(0, self._processing_complete, result, output_path)
            
        except Exception as e:
            self.root.after(0, self._processing_error, str(e))
    
    def _processing_complete(self, result, output_path):
        """Handle processing completion"""
        self.progress.stop()
        
        if result.returncode == 0 and os.path.exists(output_path):
            self.status_label.config(text=f"✅ Success! Saved: {os.path.basename(output_path)}")
            
            # Ask if user wants to open output folder
            if messagebox.askyesno("Success", f"Watermarks removed successfully!\n\nOutput: {output_path}\n\nOpen output folder?"):
                folder = os.path.dirname(output_path)
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
        else:
            self.status_label.config(text="❌ Processing failed")
            messagebox.showerror("Error", f"Processing failed:\n{result.stderr[:300]}")
    
    def _processing_error(self, error_msg):
        """Handle processing error"""
        self.progress.stop()
        self.status_label.config(text="❌ Processing error")
        messagebox.showerror("Error", f"Processing error:\n{error_msg}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🎬 Visual Watermark Remover Tool")
    print("=" * 40)
    
    # Check dependencies
    missing_packages = []
    
    try:
        import cv2
    except ImportError:
        missing_packages.append("opencv-python")
    
    try:
        from PIL import Image
    except ImportError:
        missing_packages.append("Pillow")
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("\n🔧 Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ FFmpeg not found - required for video processing")
        print("📥 Install FFmpeg:")
        print("• Windows: winget install FFmpeg")
        print("• Mac: brew install ffmpeg")
        print("• Linux: sudo apt install ffmpeg")
        return
    
    print("✅ All dependencies found!")
    print("🚀 Starting Visual Watermark Remover...")
    
    # Create and run the application
    app = VisualWatermarkRemover()
    app.run()

if __name__ == "__main__":
    main()