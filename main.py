import argparse
import logging
from pathlib import Path
from datetime import datetime
from pdf_processor import extract_text_and_images
from merger import merge_inspection_thermal
from llm_structurer import generate_ddr_structured
from report_generator import generate_markdown_report

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(inspection_pdf: str, thermal_pdf: str, property_address: str, debug_mode: bool = False):
    """
    Main function to generate DDR report with debugging and validation
    
    Args:
        inspection_pdf (str): Path to inspection PDF
        thermal_pdf (str): Path to thermal PDF
        property_address (str): Property address
        debug_mode (bool): Enable debug output
    """
    start_time = datetime.now()
    logger.info("Starting DDR generation process")
    logger.info(f"Debug mode: {'Enabled' if debug_mode else 'Disabled'}")
    
    try:
        # Create debug directory if needed
        if debug_mode:
            Path("output/debug").mkdir(parents=True, exist_ok=True)
        
        # Step 1: Extract data from both PDFs
        logger.info("Step 1: Extracting data from inspection PDF")
        print("Extracting Inspection Report...")
        insp_data = extract_text_and_images(inspection_pdf, "output/images", debug_mode)
        
        logger.info("Step 2: Extracting data from thermal PDF")
        print("Extracting Thermal Report...")
        therm_data = extract_text_and_images(thermal_pdf, "output/images", debug_mode)
        
        # Step 3: Merge the data
        logger.info("Step 3: Merging inspection and thermal data")
        print("Merging data...")
        merged = merge_inspection_thermal(insp_data, therm_data, debug_mode)
        
        # Step 4: Generate structured DDR with LLM
        logger.info("Step 4: Generating structured DDR with LLM")
        print("Generating structured DDR with LLM...")
        structured_report = generate_ddr_structured(merged, property_address, debug_mode)
        
        # Step 5: Save report
        logger.info("Step 5: Saving report")
        output_file = f"output/reports/DDR_{Path(inspection_pdf).stem}.md"
        success = generate_markdown_report(structured_report, "output/images", output_file, debug_mode)
        
        processing_time = datetime.now() - start_time
        logger.info(f"Completed DDR generation in {processing_time.total_seconds():.2f} seconds")
        
        if debug_mode and success:
            # Save intermediate results for debugging
            try:
                import json
                with open("output/debug/final_merged_data.json", "w") as f:
                    json.dump(merged, f, indent=2, default=str)
                logger.info("Saved final merged data to debug file")
            except Exception as e:
                logger.error(f"Failed to save debug JSON: {e}")
        
        if success:
            print("✅ DDR Generated Successfully!")
        else:
            print("❌ DDR Generation Completed with Errors - Check Logs")
            
    except Exception as e:
        error_msg = f"Failed to generate DDR: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate Damp Diagnosis Report (DDR)")
    parser.add_argument("--inspection-pdf", default="inspection_report.pdf", 
                        help="Path to inspection PDF (default: inspection_report.pdf)")
    parser.add_argument("--thermal-pdf", default="thermal_report.pdf", 
                        help="Path to thermal PDF (default: thermal_report.pdf)")
    parser.add_argument("--property-address", default="123 Example Street, Pune",
                        help="Property address (default: 123 Example Street, Pune)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode for detailed logging and intermediate outputs")
    
    args = parser.parse_args()
    
    # Run main function with arguments
    main(args.inspection_pdf, args.thermal_pdf, args.property_address, args.debug)
