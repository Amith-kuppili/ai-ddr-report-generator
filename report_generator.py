from pathlib import Path
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_report_content(structured_text: str) -> dict:
    """
    Validate report content to ensure it meets DDR requirements
    
    Args:
        structured_text (str): The structured text to validate
        
    Returns:
        dict: Validation results
    """
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check if structured text is empty
    if not structured_text or not structured_text.strip():
        validation_results["is_valid"] = False
        validation_results["errors"].append("Report content is empty")
        return validation_results
    
    # Check for error indicators
    if "[ERROR]" in structured_text:
        validation_results["is_valid"] = False
        validation_results["errors"].append("Report contains error messages")
    
    # Check for incomplete indicators
    if "[INCOMPLETE DDR]" in structured_text:
        validation_results["is_valid"] = False
        validation_results["errors"].append("Report marked as incomplete")
    
    # Check for required sections
    required_sections = [
        "Property Issue Summary",
        "Area-wise Observations", 
        "Probable Root Cause",
        "Severity Assessment",
        "Recommended Actions",
        "Additional Notes",
        "Missing Information"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in structured_text:
            missing_sections.append(section)
    
    if missing_sections:
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Missing required sections: {', '.join(missing_sections)}")
    
    return validation_results

def generate_markdown_report(structured_text: str, images_dir: str, output_path: str, debug_mode: bool = False):
    """
    Generate markdown report with validation and error handling
    
    Args:
        structured_text (str): The structured DDR text
        images_dir (str): Directory containing images
        output_path (str): Path to save the report
        debug_mode (bool): Enable debug output
        
    Returns:
        bool: True if report was generated successfully, False otherwise
    """
    start_time = datetime.now()
    logger.info(f"Starting report generation: {output_path}")
    
    try:
        # Validate report content
        logger.info("Validating report content")
        validation = validate_report_content(structured_text)
        
        if not validation["is_valid"]:
            logger.error(f"Report validation failed: {validation['errors']}")
            # Still generate the report but mark it as incomplete
            structured_text = f"# INCOMPLETE DDR - VALIDATION FAILED\n\nErrors: {', '.join(validation['errors'])}\n\n{structured_text}"
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
        
        # Generate the report
        logger.info("Writing report to file")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Damp Diagnosis Report (DDR)\n\n")
            f.write(structured_text)
        
        processing_time = datetime.now() - start_time
        logger.info(f"Successfully generated report in {processing_time.total_seconds():.2f} seconds")
        print(f"Report saved to: {output_path}")
        
        if debug_mode:
            debug_info = {
                "generation_start_time": start_time.isoformat(),
                "generation_end_time": datetime.now().isoformat(),
                "processing_time": str(processing_time),
                "validation_passed": validation["is_valid"],
                "validation_errors": validation["errors"],
                "file_size_bytes": os.path.getsize(output_path)
            }
            logger.info(f"Debug info: {debug_info}")
            
            # Save debug information
            debug_output_path = output_path.replace(".md", "_debug.json")
            try:
                import json
                with open(debug_output_path, "w") as f:
                    json.dump(debug_info, f, indent=2)
                logger.info(f"Debug info saved to: {debug_output_path}")
            except Exception as e:
                logger.error(f"Failed to save debug info: {e}")
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to generate report: {e}"
        logger.error(error_msg)
        print(error_msg)
        return False
