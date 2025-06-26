import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import threading
import time
import os
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import base64
from io import BytesIO

# Set the theme and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ToastNotification:
    def __init__(self, parent, message, duration=3000):
        self.parent = parent
        self.toast = ctk.CTkToplevel(parent)
        self.toast.withdraw()
        
        # Configure toast window
        self.toast.overrideredirect(True)
        self.toast.configure(fg_color=("#3B8ED0", "#1F6AA5"))
        
        # Create toast content
        toast_label = ctk.CTkLabel(
            self.toast,
            text=message,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        toast_label.pack(padx=20, pady=10)
        
        # Position toast
        self.show_toast()
        
        # Auto-hide after duration
        self.toast.after(duration, self.hide_toast)
    
    def show_toast(self):
        self.toast.update_idletasks()
        width = self.toast.winfo_reqwidth()
        height = self.toast.winfo_reqheight()
        
        # Position at top-right of parent window
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        
        x = parent_x + parent_width - width - 20
        y = parent_y + 50
        
        self.toast.geometry(f"{width}x{height}+{x}+{y}")
        self.toast.deiconify()
        self.toast.lift()
    
    def hide_toast(self):
        self.toast.destroy()

class EDAAnalyzer:
    def __init__(self, df):
        self.df = df
        self.analysis_results = {}
    
    def perform_analysis(self, progress_callback=None):
        """Perform comprehensive EDA analysis with progress updates"""
        results = {}
        
        # Step 1: Basic info
        if progress_callback:
            progress_callback(10, "Analyzing basic dataset information...")
        results['shape'] = self.df.shape
        results['columns'] = list(self.df.columns)
        results['dtypes'] = self.df.dtypes.to_dict()
        results['memory_usage'] = self.df.memory_usage(deep=True).sum()
        
        # Step 2: Missing values
        if progress_callback:
            progress_callback(25, "Checking for missing values...")
        results['missing_values'] = self.df.isnull().sum().to_dict()
        results['missing_percentage'] = (self.df.isnull().sum() / len(self.df) * 100).to_dict()
        
        # Step 3: Numerical columns analysis
        if progress_callback:
            progress_callback(50, "Analyzing numerical columns...")
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            results['numeric_summary'] = self.df[numeric_cols].describe().to_dict()
            results['correlation_matrix'] = self.df[numeric_cols].corr().to_dict()
        
        # Step 4: Categorical columns analysis
        if progress_callback:
            progress_callback(75, "Analyzing categorical columns...")
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        if cat_cols:
            results['categorical_summary'] = {}
            for col in cat_cols:
                results['categorical_summary'][col] = {
                    'unique_count': self.df[col].nunique(),
                    'top_values': self.df[col].value_counts().head(10).to_dict()
                }
        
        # Step 5: Duplicate rows
        if progress_callback:
            progress_callback(90, "Checking for duplicate rows...")
        results['duplicate_rows'] = self.df.duplicated().sum()
        
        if progress_callback:
            progress_callback(100, "Analysis complete!")
        
        self.analysis_results = results
        return results

class QuickEDAApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Quick EDA - Exploratory Data Analysis Tool")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # App state
        self.uploaded_file_path = None
        self.df = None
        self.analysis_results = None
        self.report_generated = False
        self.analysis_in_progress = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI"""
        # Main container with scrollable frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create scrollable frame that covers the entire main area
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Quick EDA",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Upload your data file and generate comprehensive EDA reports",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Create sections
        self.create_upload_section()
        self.create_analysis_section()
        self.create_download_section()
        self.create_reset_section()
    
    def create_upload_section(self):
        """Create file upload section"""
        # Upload section frame
        self.upload_frame = ctk.CTkFrame(self.scrollable_frame)
        self.upload_frame.pack(fill="x", pady=(0, 20))
        
        # Section header
        upload_header = ctk.CTkLabel(
            self.upload_frame,
            text="📁 Step 1: Upload Data File",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        upload_header.pack(pady=(20, 10))
        
        # Upload button
        self.upload_btn = ctk.CTkButton(
            self.upload_frame,
            text="Choose File (CSV, XLSX, TXT)",
            command=self.upload_file,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.upload_btn.pack(pady=10)
        
        # File info label
        self.file_info_label = ctk.CTkLabel(
            self.upload_frame,
            text="No file selected",
            font=ctk.CTkFont(size=12)
        )
        self.file_info_label.pack(pady=5)
        
        # Remove file button (initially hidden)
        self.remove_file_btn = ctk.CTkButton(
            self.upload_frame,
            text="Remove File",
            command=self.remove_file,
            fg_color="red",
            hover_color="darkred",
            height=30
        )
        
        # Upload progress bar
        self.upload_progress = ctk.CTkProgressBar(self.upload_frame)
        
    def create_analysis_section(self):
        """Create analysis section"""
        self.analysis_frame = ctk.CTkFrame(self.scrollable_frame)
        self.analysis_frame.pack(fill="x", pady=(0, 20))
        
        # Section header
        analysis_header = ctk.CTkLabel(
            self.analysis_frame,
            text="📊 Step 2: Analyze Data",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        analysis_header.pack(pady=(20, 10))
        
        # Analyze button
        self.analyze_btn = ctk.CTkButton(
            self.analysis_frame,
            text="Analyse Data",
            command=self.analyze_data,
            height=40,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.analyze_btn.pack(pady=10)
        
        # Analysis progress bar
        self.analysis_progress = ctk.CTkProgressBar(self.analysis_frame)
        
        # Analysis status label
        self.analysis_status_label = ctk.CTkLabel(
            self.analysis_frame,
            text="Upload a file to begin analysis",
            font=ctk.CTkFont(size=12)
        )
        self.analysis_status_label.pack(pady=5)
        
        # Detailed progress label
        self.analysis_detail_label = ctk.CTkLabel(
            self.analysis_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
    
    def create_download_section(self):
        """Create download section"""
        self.download_frame = ctk.CTkFrame(self.scrollable_frame)
        self.download_frame.pack(fill="x", pady=(0, 20))
        
        # Section header
        download_header = ctk.CTkLabel(
            self.download_frame,
            text="📄 Step 3: Download Report",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        download_header.pack(pady=(20, 10))
        
        # File name input
        self.filename_entry = ctk.CTkEntry(
            self.download_frame,
            placeholder_text="Enter report filename (without extension)",
            width=300,
            height=35
        )
        self.filename_entry.pack(pady=5)
        
        # Download button
        self.download_btn = ctk.CTkButton(
            self.download_frame,
            text="Download Report",
            command=self.download_report,
            height=40,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.download_btn.pack(pady=10)
        
        # Download status label
        self.download_status_label = ctk.CTkLabel(
            self.download_frame,
            text="Complete analysis to download report",
            font=ctk.CTkFont(size=12)
        )
        self.download_status_label.pack(pady=5)
    
    def create_reset_section(self):
        """Create reset section"""
        self.reset_frame = ctk.CTkFrame(self.scrollable_frame)
        self.reset_frame.pack(fill="x", pady=(0, 20))
        
        # Reset button
        self.reset_btn = ctk.CTkButton(
            self.reset_frame,
            text="🔁 Analyse Another File",
            command=self.reset_app,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="orange",
            hover_color="darkorange"
        )
        self.reset_btn.pack(pady=20)
    
    def upload_file(self):
        """Handle file upload"""
        file_types = [
            ("All Supported", "*.csv;*.xlsx;*.xls;*.txt"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx;*.xls"),
            ("Text files", "*.txt")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select data file",
            filetypes=file_types
        )
        
        if file_path:
            self.upload_progress.pack(pady=10)
            self.upload_progress.set(0)
            
            # Simulate upload progress in a separate thread
            thread = threading.Thread(target=self.process_upload, args=(file_path,))
            thread.daemon = True
            thread.start()
    
    def process_upload(self, file_path):
        """Process file upload with progress"""
        try:
            # Simulate progress
            for i in range(101):
                self.upload_progress.set(i / 100)
                time.sleep(0.01)  # Small delay for visual effect
            
            # Load the file
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                self.df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(file_path)
            elif file_ext == '.txt':
                # Try to read as CSV first, then as plain text
                try:
                    self.df = pd.read_csv(file_path, sep='\t')
                except:
                    self.df = pd.read_csv(file_path)
            
            self.uploaded_file_path = file_path
            
            # Update UI in main thread
            self.root.after(0, self.upload_success)
            
        except Exception as e:
            self.root.after(0, lambda: self.upload_error(str(e)))
    
    def upload_success(self):
        """Handle successful upload"""
        filename = os.path.basename(self.uploaded_file_path)
        rows, cols = self.df.shape
        
        self.file_info_label.configure(
            text=f"✅ {filename} ({rows:,} rows, {cols} columns)"
        )
        
        self.upload_progress.pack_forget()
        self.remove_file_btn.pack(pady=5)
        
        # Enable analysis button
        self.analyze_btn.configure(state="normal")
        self.analysis_status_label.configure(text="Ready to analyse data")
        
        # Show success toast
        ToastNotification(self.root, "File uploaded successfully!")
    
    def upload_error(self, error_msg):
        """Handle upload error"""
        self.upload_progress.pack_forget()
        messagebox.showerror("Upload Error", f"Failed to load file:\n{error_msg}")
    
    def remove_file(self):
        """Remove uploaded file"""
        self.uploaded_file_path = None
        self.df = None
        self.analysis_results = None
        self.report_generated = False
        
        # Reset UI
        self.file_info_label.configure(text="No file selected")
        self.remove_file_btn.pack_forget()
        self.analyze_btn.configure(state="disabled")
        self.analysis_status_label.configure(text="Upload a file to begin analysis")
        self.analysis_detail_label.configure(text="")
        self.analysis_detail_label.pack_forget()
        self.download_btn.configure(state="disabled")
        self.download_status_label.configure(text="Complete analysis to download report")
        
        # Show success toast
        ToastNotification(self.root, "File removed successfully!")
    
    def analyze_data(self):
        """Analyze the uploaded data"""
        if self.df is None or self.analysis_in_progress:
            return
        
        self.analysis_in_progress = True
        self.analysis_progress.pack(pady=10)
        self.analysis_detail_label.pack(pady=5)
        self.analysis_progress.set(0)
        self.analysis_status_label.configure(text="🔄 Analyzing data...")
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self.process_analysis)
        thread.daemon = True
        thread.start()
    
    def update_analysis_progress(self, progress, detail_text):
        """Update analysis progress from background thread"""
        self.analysis_progress.set(progress / 100)
        self.analysis_detail_label.configure(text=detail_text)
        self.root.update_idletasks()
    
    def process_analysis(self):
        """Process data analysis with progress"""
        try:
            analyzer = EDAAnalyzer(self.df)
            
            # Perform actual analysis with progress updates
            def progress_callback(progress, detail):
                self.root.after(0, lambda: self.update_analysis_progress(progress, detail))
                time.sleep(0.5)  # Add some delay to show progress
            
            self.analysis_results = analyzer.perform_analysis(progress_callback)
            
            # Update UI in main thread
            self.root.after(0, self.analysis_success)
            
        except Exception as e:
            self.root.after(0, lambda: self.analysis_error(str(e)))
    
    def analysis_success(self):
        """Handle successful analysis"""
        self.analysis_in_progress = False
        self.analysis_progress.pack_forget()
        self.analysis_detail_label.pack_forget()
        self.analysis_status_label.configure(text="✅ Analysis completed successfully!")
        self.analyze_btn.configure(state="normal", text="Re-analyze Data")
        
        # Enable download button
        self.download_btn.configure(state="normal")
        self.download_status_label.configure(text="Ready to download report")
        
        # Set default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"EDA_Report_{timestamp}"
        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, default_name)
        
        # Show success toast
        ToastNotification(self.root, "Analysis Completed Successfully!")
    
    def analysis_error(self, error_msg):
        """Handle analysis error"""
        self.analysis_in_progress = False
        self.analysis_progress.pack_forget()
        self.analysis_detail_label.pack_forget()
        self.analysis_status_label.configure(text="❌ Analysis failed")
        self.analyze_btn.configure(state="normal", text="Analyse Data")
        messagebox.showerror("Analysis Error", f"Failed to analyze data:\n{error_msg}")
    
    def download_report(self):
        """Download the EDA report as PDF"""
        if not self.analysis_results:
            return
        
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showwarning("Input Required", "Please enter a filename for the report")
            return
        
        # Choose save location - FIXED: Use initialfile instead of initialvalue
        save_path = filedialog.asksaveasfilename(
            title="Save EDA Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{filename}.pdf"  # Changed from initialvalue to initialfile
        )
        
        if save_path:
            try:
                self.generate_pdf_report(save_path)
                self.download_status_label.configure(text=f"✅ Report saved to: {os.path.basename(save_path)}")
                ToastNotification(self.root, "Report saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save report:\n{str(e)}")
    
    def generate_pdf_report(self, save_path):
        """Generate comprehensive PDF report"""
        doc = SimpleDocTemplate(save_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1f77b4')
        )
        
        # Title
        story.append(Paragraph("Exploratory Data Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Generated info
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        if self.uploaded_file_path:
            story.append(Paragraph(f"Source file: {os.path.basename(self.uploaded_file_path)}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Dataset Overview
        story.append(Paragraph("Dataset Overview", heading_style))
        overview_data = [
            ['Metric', 'Value'],
            ['Number of Rows', f"{self.analysis_results['shape'][0]:,}"],
            ['Number of Columns', f"{self.analysis_results['shape'][1]}"],
            ['Memory Usage', f"{self.analysis_results['memory_usage'] / 1024 / 1024:.2f} MB"],
            ['Duplicate Rows', f"{self.analysis_results['duplicate_rows']:,}"]
        ]
        
        overview_table = Table(overview_data)
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 20))
        
        # Column Information
        story.append(Paragraph("Column Information", heading_style))
        col_data = [['Column Name', 'Data Type', 'Missing Values', 'Missing %']]
        
        for col in self.analysis_results['columns']:
            missing_count = self.analysis_results['missing_values'][col]
            missing_pct = self.analysis_results['missing_percentage'][col]
            col_data.append([
                col,
                str(self.analysis_results['dtypes'][col]),
                str(missing_count),
                f"{missing_pct:.1f}%"
            ])
        
        col_table = Table(col_data)
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8)
        ]))
        story.append(col_table)
        
        # Numerical Summary
        if 'numeric_summary' in self.analysis_results:
            story.append(PageBreak())
            story.append(Paragraph("Numerical Columns Summary", heading_style))
            
            numeric_data = [['Column', 'Count', 'Mean', 'Std', 'Min', '25%', '50%', '75%', 'Max']]
            
            for col, stats in self.analysis_results['numeric_summary'].items():
                numeric_data.append([
                    col,
                    f"{stats['count']:.0f}",
                    f"{stats['mean']:.2f}",
                    f"{stats['std']:.2f}",
                    f"{stats['min']:.2f}",
                    f"{stats['25%']:.2f}",
                    f"{stats['50%']:.2f}",
                    f"{stats['75%']:.2f}",
                    f"{stats['max']:.2f}"
                ])
            
            numeric_table = Table(numeric_data)
            numeric_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7)
            ]))
            story.append(numeric_table)
        
        # Categorical Summary
        if 'categorical_summary' in self.analysis_results:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Categorical Columns Summary", heading_style))
            
            for col, info in self.analysis_results['categorical_summary'].items():
                story.append(Paragraph(f"Column: {col}", styles['Heading2']))
                story.append(Paragraph(f"Unique values: {info['unique_count']}", styles['Normal']))
                
                # Top values
                if info['top_values']:
                    story.append(Paragraph("Top values:", styles['Normal']))
                    top_data = [['Value', 'Count']]
                    for value, count in list(info['top_values'].items())[:5]:
                        top_data.append([str(value)[:30], str(count)])  # Limit value length
                    
                    top_table = Table(top_data)
                    top_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(top_table)
                    story.append(Spacer(1, 10))
        
        # Generate PDF
        doc.build(story)
    
    def reset_app(self):
        """Reset the application to initial state"""
        self.remove_file()
        ToastNotification(self.root, "Application reset successfully!")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check for required libraries
    required_libs = ['customtkinter', 'pandas', 'reportlab', 'matplotlib', 'seaborn']
    missing_libs = []
    
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        print("Missing required libraries:")
        for lib in missing_libs:
            print(f"  pip install {lib}")
        print("\nPlease install the missing libraries and run again.")
    else:
        app = QuickEDAApp()
        app.run()