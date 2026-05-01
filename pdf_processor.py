import fitz  # PyMuPDF
import pdfplumber
import os
from pathlib import Path
from PIL import Image
import io
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_and_images(pdf_path: str, output_img_dir: str = "output/images", debug_mode: bool = False):
    """
    Extract text and images from PDF with comprehensive logging and error handling
    
    Args:
        pdf_path (str): Path to the PDF file
        output_img_dir (str): Directory to save extracted images
        debug_mode (bool): Enable debug output
        
    Returns:
        dict: Dictionary containing extracted text, images, and metadata
    """
    start_time = datetime.now()
    logger.info(f"Starting PDF processing for: {pdf_path}")
    
    try:
        Path(output_img_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified image output directory: {output_img_dir}")
    except Exception as e:
        logger.error(f"Failed to create image output directory: {e}")
        raise
    
    # Initialize result containers
    full_text = []
    images = []
    errors = []
    
    try:
        doc = fitz.open(pdf_path)
        logger.info(f"Opened PDF document with {len(doc)} pages")
    except Exception as e:
        logger.error(f"Failed to open PDF document: {e}")
        raise
    
    # Process each page
    for page_num in range(len(doc)):
        page_start_time = datetime.now()
        page = doc[page_num]
        logger.info(f"Processing page {page_num + 1}/{len(doc)}")
        
        # Text extraction - best quality
        try:
            text = page.get_text("text")
            if text.strip():
                full_text.append(f"--- Page {page_num+1} ---\n{text}")
                logger.debug(f"Extracted {len(text)} characters from page {page_num+1}")
            else:
                logger.warning(f"No text found on page {page_num+1}")
                full_text.append(f"--- Page {page_num+1} ---\n[No text content]")
        except Exception as e:
            error_msg = f"Error extracting text from page {page_num}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            full_text.append(f"--- Page {page_num+1} ---\n[Text extraction failed]")
        
        # Better structured text with pdfplumber for tables/observations
        try:
            with pdfplumber.open(pdf_path) as plumber_pdf:
                plumber_page = plumber_pdf.pages[page_num]
                table_text = plumber_page.extract_text() or ""
                if table_text:
                    full_text.append(f"[Structured]\n{table_text}")
                    logger.debug(f"Extracted structured text ({len(table_text)} chars) from page {page_num+1}")
        except Exception as e:
            error_msg = f"Error extracting structured text from page {page_num}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Image extraction
        try:
            image_list = page.get_images(full=True)
            logger.info(f"Found {len(image_list)} images on page {page_num+1}")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    img_ext = base_image["ext"]
                    
                    img_filename = f"{Path(pdf_path).stem}_p{page_num+1}_img{img_index+1}.{img_ext}"
                    img_path = os.path.join(output_img_dir, img_filename)
                    
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)
                    
                    # Optional: also save as PNG for consistency in report
                    if img_ext.lower() != "png":
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        png_path = img_path.rsplit(".", 1)[0] + ".png"
                        pil_img.save(png_path)
                        img_path = png_path
                    
                    images.append({
                        "page": page_num + 1,
                        "path": img_path,
                        "filename": os.path.basename(img_path),
                        "type": "thermal" if "thermal" in pdf_path.lower() else "visual",
                        "source_document": pdf_path
                    })
                    logger.debug(f"Saved image: {img_filename}")
                except Exception as e:
                    error_msg = f"Error extracting image {img_index+1} on page {page_num}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error processing images on page {page_num}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    processing_time = datetime.now() - start_time
    logger.info(f"Completed PDF processing in {processing_time.total_seconds():.2f} seconds")
    logger.info(f"Extracted {len(full_text)} text sections and {len(images)} images")
    
    if debug_mode:
        debug_info = {
            "processing_time": str(processing_time),
            "pages_processed": len(doc),
            "text_sections": len(full_text),
            "images_extracted": len(images),
            "errors_encountered": errors
        }
        logger.info(f"Debug info: {debug_info}")
    
    return {
        "text": "\n\n".join(full_text),
        "images": images,
        "filename": Path(pdf_path).stem,
        "debug_info": {
            "processing_time": str(processing_time),
            "pages_processed": len(doc),
            "text_sections": len(full_text),
            "images_extracted": len(images),
            "errors_encountered": errors
        } if debug_mode else None
    }
