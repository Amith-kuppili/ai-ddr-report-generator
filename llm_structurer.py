import os
import logging
import json
from datetime import datetime
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """You are an expert building damp diagnosis surveyor with 15+ years experience.
You combine visual inspection findings with thermal imaging data to produce accurate, honest DDR reports.

Rules:
- Never hallucinate issues or images.
- If data conflicts, clearly flag it.
- Use simple, non-technical language where possible.
- Be precise and evidence-based.
- Structure output exactly as requested.

Input Format:
Property: {property_address}

Combined Extracted Data:
{text_data}

Images Available:
{image_list}

Generate a professional Damp Diagnosis Report (DDR) in this EXACT structure:

1. Property Issue Summary
   (2-4 bullet points of major findings)

2. Area-wise Observations
   - Area Name
     - Visual Inspection:
     - Thermal Anomalies:
     - Supporting Images: [list filenames or "Image Not Available"]

3. Probable Root Cause
   (Most likely causes with reasoning)

4. Severity Assessment
   (Low / Medium / High for each major issue)

5. Recommended Actions
   (Prioritized - Immediate / Short term / Monitoring)

6. Additional Notes

7. Missing Information
   (What data was not available in the reports)"""

def validate_ddr_output(ddr_text: str) -> dict:
    """
    Validate DDR output to ensure all required sections are present
    
    Args:
        ddr_text (str): Generated DDR text
        
    Returns:
        dict: Validation results with any missing sections
    """
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
        if section not in ddr_text:
            missing_sections.append(section)
    
    validation_result = {
        "is_valid": len(missing_sections) == 0,
        "missing_sections": missing_sections,
        "total_sections_required": len(required_sections),
        "sections_provided": len(required_sections) - len(missing_sections)
    }
    
    return validation_result

def generate_ddr_structured(merged_data: dict, property_address: str = "Property Address", debug_mode: bool = False):
    """
    Generate structured DDR with validation and error handling
    
    Args:
        merged_data (dict): Merged inspection and thermal data
        property_address (str): Property address for the report
        debug_mode (bool): Enable debug output
        
    Returns:
        str: Validated DDR text or error message
    """
    start_time = datetime.now()
    logger.info("Starting DDR generation with LLM")
    
    try:
        # Extract image filenames for the prompt
        image_list = [img['filename'] for img in merged_data.get('all_images', [])]
        logger.info(f"Found {len(image_list)} images for reference")
        
        user_content = f"""
Property: {property_address}

Combined Extracted Data:
{merged_data}

Images Available:
{image_list}

Generate a professional Damp Diagnosis Report (DDR) in this EXACT structure:

1. Property Issue Summary
   (2-4 bullet points of major findings)

2. Area-wise Observations
   - Area Name
     - Visual Inspection:
     - Thermal Anomalies:
     - Supporting Images: [list filenames or "Image Not Available"]

3. Probable Root Cause
   (Most likely causes with reasoning)

4. Severity Assessment
   (Low / Medium / High for each major issue)

5. Recommended Actions
   (Prioritized - Immediate / Short term / Monitoring)

6. Additional Notes

7. Missing Information
   (What data was not available in the reports)
"""
        
        logger.info("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-4o-mini for cost
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,  # Low temperature for reproducibility
            max_tokens=2500
        )
        
        ddr_text = response.choices[0].message.content
        logger.info("Received response from OpenAI API")
        
        # Validate the output
        logger.info("Validating DDR output")
        validation_result = validate_ddr_output(ddr_text)
        
        if not validation_result["is_valid"]:
            logger.warning(f"DDR validation failed. Missing sections: {validation_result['missing_sections']}")
            # Add a note about missing sections
            ddr_text += f"\n\n[INCOMPLETE DDR - Missing sections: {', '.join(validation_result['missing_sections'])}]"
        else:
            logger.info("DDR validation passed - all sections present")
        
        processing_time = datetime.now() - start_time
        logger.info(f"Completed DDR generation in {processing_time.total_seconds():.2f} seconds")
        
        if debug_mode:
            debug_info = {
                "generation_start_time": start_time.isoformat(),
                "generation_end_time": datetime.now().isoformat(),
                "processing_time": str(processing_time),
                "model_used": "gpt-4o",
                "temperature": 0.1,
                "validation_result": validation_result,
                "token_usage": response.usage if hasattr(response, 'usage') else "Unknown"
            }
            logger.info(f"Debug info: {debug_info}")
            
            # Save intermediate JSON for debugging
            try:
                with open("output/debug/merged_data.json", "w") as f:
                    json.dump(merged_data, f, indent=2)
                logger.info("Saved merged data to debug file")
            except Exception as e:
                logger.error(f"Failed to save debug JSON: {e}")
        
        return ddr_text
        
    except OpenAIError as e:
        error_msg = f"OpenAI API error: {e}"
        logger.error(error_msg)
        return f"[ERROR] Failed to generate DDR: {error_msg}"
        
    except Exception as e:
        error_msg = f"Unexpected error during DDR generation: {e}"
        logger.error(error_msg)
        return f"[ERROR] Failed to generate DDR: {error_msg}"
