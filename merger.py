import logging
from collections import defaultdict
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_issue(text: str) -> str:
    """Simple normalization for common damp/moisture terms"""
    text = text.lower().strip()
    mappings = {
        "seepage": "moisture ingress",
        "dampness": "damp patch",
        "water stain": "water marking",
        "efflorescence": "salt deposit",
        "mould": "mold growth",
        "condensation": "condensation",
    }
    for k, v in mappings.items():
        if k in text:
            return v.capitalize()
    return text.capitalize()

def detect_conflicts(inspection_text: str, thermal_text: str) -> list:
    """
    Detect conflicts between inspection and thermal reports
    """
    conflicts = []
    
    # Common conflicting patterns
    conflict_patterns = [
        (r"(no|zero|none).*damp", r"(high|significant).*temperature.*difference"),
        (r"(dry|no moisture)", r"(wet|moist).*reading"),
        (r"(structurally sound)", r"(crack|damage|degradation)")
    ]
    
    for insp_pattern, therm_pattern in conflict_patterns:
        if re.search(insp_pattern, inspection_text, re.IGNORECASE) and \
           re.search(therm_pattern, thermal_text, re.IGNORECASE):
            conflicts.append(f"Potential conflict: {insp_pattern} vs {therm_pattern}")
    
    return conflicts

def merge_inspection_thermal(inspection_data: dict, thermal_data: dict, debug_mode: bool = False):
    """
    Merge inspection and thermal data with logging, conflict detection, and traceability
    
    Args:
        inspection_data (dict): Data from inspection report
        thermal_data (dict): Data from thermal report
        debug_mode (bool): Enable debug output
        
    Returns:
        dict: Merged data with traceability information
    """
    start_time = datetime.now()
    logger.info("Starting data merging process")
    
    # Initialize result containers
    merged = {
        "summary_issues": [],
        "area_wise": defaultdict(dict),
        "conflicts": [],
        "missing": [],
        "traceability": {}  # For tracking source documents and pages
    }
    
    if debug_mode:
        merged["debug_info"] = {
            "merge_start_time": start_time.isoformat(),
            "inspection_source": inspection_data.get("filename", "Unknown"),
            "thermal_source": thermal_data.get("filename", "Unknown")
        }
    
    # Extract potential areas (Living Room, Bedroom, Kitchen, Wall, Ceiling, etc.)
    area_pattern = re.compile(r'(living room|bedroom|kitchen|bathroom|toilet|hall|ceiling|wall|floor|roof|exterior)', re.I)
    
    def extract_areas(text):
        found = area_pattern.findall(text)
        return list(set([area.capitalize() for area in found])) or ["General"]
    
    logger.info("Extracting areas from inspection and thermal reports")
    insp_areas = extract_areas(inspection_data["text"])
    therm_areas = extract_areas(thermal_data["text"])
    all_areas = list(set(insp_areas + therm_areas))
    
    logger.info(f"Found {len(all_areas)} unique areas: {all_areas}")
    
    # Detect conflicts between reports
    logger.info("Detecting conflicts between inspection and thermal data")
    conflicts = detect_conflicts(inspection_data["text"], thermal_data["text"])
    if conflicts:
        logger.warning(f"Detected {len(conflicts)} potential conflicts")
        merged["conflicts"] = conflicts
        for conflict in conflicts:
            logger.info(f"Conflict detected between Inspection and Thermal data: {conflict}")
    
    # Combine all images with traceability
    logger.info("Combining images from both reports")
    all_images = []
    for img in inspection_data["images"] + thermal_data["images"]:
        all_images.append({
            "page": img["page"],
            "path": img["path"],
            "filename": img["filename"],
            "type": img["type"],
            "source_document": img.get("source_document", "Unknown"),
            "trace_id": f"{img.get('source_document', 'unknown')}_{img['page']}_{img['filename']}"
        })
    
    # Area-based merging with traceability
    logger.info("Performing area-based merging")
    for area in all_areas:
        logger.debug(f"Processing area: {area}")
        
        # Extract area-specific information with traceability
        area_trace = {
            "area_name": area,
            "inspection_source_pages": [],
            "thermal_source_pages": [],
            "images": []
        }
        
        # Find relevant text sections for this area
        insp_area_text = ""
        therm_area_text = ""
        
        # Simple heuristic to find area-relevant text
        for line in inspection_data["text"].split('\n'):
            if area.lower() in line.lower():
                insp_area_text += line + "\n"
                # Try to extract page number
                page_match = re.search(r"Page (\d+)", line)
                if page_match:
                    area_trace["inspection_source_pages"].append(int(page_match.group(1)))
        
        for line in thermal_data["text"].split('\n'):
            if area.lower() in line.lower():
                therm_area_text += line + "\n"
                # Try to extract page number
                page_match = re.search(r"Page (\d+)", line)
                if page_match:
                    area_trace["thermal_source_pages"].append(int(page_match.group(1)))
        
        # Find area-specific images
        area_images = [img for img in all_images 
                      if area.lower() in img["filename"].lower() or 
                         area.lower() in img.get("source_document", "").lower() or
                         True]  # fallback to all images if none match
        
        # Add traceability information
        for img in area_images:
            area_trace["images"].append(img["trace_id"])
        
        # Store merged area data
        merged["area_wise"][area] = {
            "inspection_issues": insp_area_text.strip() if insp_area_text.strip() else "Not Available",
            "thermal_anomalies": therm_area_text.strip() if therm_area_text.strip() else "Not Available",
            "images": area_images,
            "traceability": area_trace
        }
        
        # Check for missing data
        if not insp_area_text.strip():
            merged["missing"].append(f"Visual inspection data for {area}")
        if not therm_area_text.strip():
            merged["missing"].append(f"Thermal data for {area}")
    
    # Add global information
    merged["all_images"] = all_images
    merged["traceability"] = {
        "inspection_pages": len(inspection_data.get("debug_info", {}).get("pages_processed", [])) if inspection_data.get("debug_info") else "Unknown",
        "thermal_pages": len(thermal_data.get("debug_info", {}).get("pages_processed", [])) if thermal_data.get("debug_info") else "Unknown",
        "total_images": len(all_images)
    }
    
    processing_time = datetime.now() - start_time
    logger.info(f"Completed data merging in {processing_time.total_seconds():.2f} seconds")
    
    if debug_mode:
        merged["debug_info"]["merge_end_time"] = datetime.now().isoformat()
        merged["debug_info"]["processing_time"] = str(processing_time)
        merged["debug_info"]["total_areas"] = len(all_areas)
        merged["debug_info"]["total_conflicts"] = len(conflicts)
        merged["debug_info"]["total_images"] = len(all_images)
    
    return merged
