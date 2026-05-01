# Damp Diagnosis Report (DDR) Generator - System Design

## 1. High-Level Architecture

```text
Input PDFs
   ↓
Text + Image Extraction (pdf_processor.py)
   ↓
Data Cleaning & Merging (merger.py)
   ↓
LLM Processing (llm_structurer.py)
   ↓
DDR Generator (report_generator.py)
```

## 2. Components Breakdown

### 2.1 Input Ingestion
- Accepts two PDF files: inspection report and thermal report
- Validates file existence and readability
- Creates output directories if needed

### 2.2 PDF Parsing (Text + Image Extraction)
**Module**: `pdf_processor.py`

**Key Features**:
- Text extraction using PyMuPDF (fitz) for robustness
- Structured content extraction using pdfplumber for tables/lists
- Image extraction with format conversion to PNG
- Filename sanitization to prevent filesystem issues
- Debug mode for intermediate outputs

**Process**:
1. Load PDF document
2. Extract text content page by page
3. Extract images and save as PNG files
4. Associate images with page numbers
5. Return structured data with text and image paths

### 2.3 Data Cleaning & Normalization
**Module**: `merger.py`

**Key Features**:
- Area identification using keyword matching
- Issue extraction with severity tagging
- Data deduplication algorithms
- Conflict detection between visual and thermal data
- Missing data handling with "Not Available" placeholders

**Process**:
1. Parse areas from both reports
2. Extract issues with supporting evidence
3. Identify and merge duplicate findings
4. Detect conflicts between visual and thermal data
5. Structure data for LLM processing

### 2.4 Entity Extraction
**Techniques**:
- Keyword-based area identification (living room, bedroom, etc.)
- Regular expressions for issue patterns
- Temperature value extraction from thermal reports
- Severity classification (high, medium, low)

### 2.5 Data Merging Logic
**Module**: `merger.py`

**Key Algorithms**:
1. **Area Matching**: Associates findings by room/area names
2. **Duplicate Detection**: Identifies repeated issues using fuzzy matching
3. **Conflict Resolution**: Flags discrepancies between visual and thermal data
4. **Missing Data Handling**: Inserts "Not Available" for absent information

### 2.6 Conflict Resolution Module
**Features**:
- Cross-references visual and thermal findings
- Flags contradictory information (e.g., dry visual vs wet thermal)
- Generates conflict reports for manual review
- Maintains data provenance

### 2.7 LLM-Based Report Generation
**Module**: `llm_structurer.py`

**Key Features**:
- Structured prompt engineering for consistent outputs
- GPT-4 integration with error handling
- Retry mechanism for API failures
- Validation of LLM responses
- Debug mode for prompt/response analysis

**Process**:
1. Format merged data for LLM consumption
2. Send structured prompt to OpenAI API
3. Validate and clean LLM response
4. Return structured report data

### 2.8 Output Formatting (Markdown/PDF)
**Module**: `report_generator.py`

**Key Features**:
- Markdown report generation with image embedding
- Section validation to ensure completeness
- Image path resolution and verification
- Extensible to PDF/HTML formats
- Debug mode for template analysis

## 3. Tech Stack Recommendation

### 3.1 Languages
- **Python 3.9+**: Primary language for processing pipeline

### 3.2 Libraries
- **PyMuPDF (fitz)**: Robust PDF text and image extraction
- **pdfplumber**: Structured content extraction from PDFs
- **Pillow (PIL)**: Image processing and format conversion
- **OpenAI**: LLM processing for report generation
- **python-dotenv**: Environment variable management
- **pydantic**: Data validation and settings management
- **streamlit** (optional): Web interface for UI

### 3.3 Models
- **OpenAI GPT-4/GPT-4o**: Natural language processing for report generation

### 3.4 Storage
- **Local File System**: Default storage for images and reports
- **Extensible**: Can integrate with cloud storage services

## 4. Core Logic Design

### 4.1 Duplicate Handling
- **Fuzzy Matching**: Uses string similarity to identify potential duplicates
- **Area-Based Grouping**: Groups findings by room/area for comparison
- **Priority Logic**: Thermal data takes precedence in conflict resolution

### 4.2 Conflict Detection and Reporting
- **Cross-Validation**: Compares findings between visual and thermal reports
- **Discrepancy Flagging**: Marks conflicting information for manual review
- **Evidence Preservation**: Maintains source information for all findings

### 4.3 Missing Values Handling
- **Placeholder Insertion**: Uses "Not Available" for missing information
- **Section Validation**: Ensures all required sections are present
- **Graceful Degradation**: Continues processing even with partial data

### 4.4 Area-Wise Grouping
- **Keyword Matching**: Identifies rooms/areas using predefined keywords
- **Hierarchical Organization**: Groups findings under appropriate areas
- **Flexible Mapping**: Accommodates variations in area naming conventions

## 5. Image Handling Design

### 5.1 Extraction Method
- **PyMuPDF Integration**: Extracts embedded images from PDFs
- **Format Conversion**: Converts all images to PNG for consistency
- **Filename Sanitization**: Creates filesystem-safe filenames

### 5.2 Mapping Logic
- **Page Association**: Links images to specific pages in reports
- **Content Analysis**: Attempts to associate images with relevant findings
- **Fallback Mechanism**: Provides "Image Not Available" when mapping fails

### 5.3 Placement Strategy in DDR
- **Contextual Insertion**: Places images near relevant findings
- **Multiple Image Support**: Handles multiple images per observation
- **Path Management**: Manages relative paths for portability

## 6. Prompt Engineering

**Module**: `prompts/structuring_prompt.txt`

**Key Elements**:
- Explicit DDR structure specification
- Client-friendly language requirements
- Conflict highlighting instructions
- Missing data representation guidelines
- Image inclusion directives

## 7. Pseudocode / Code Skeleton

### 7.1 Extraction Process
```python
def extract_text_and_images(pdf_path, image_output_dir, debug=False):
    document = load_pdf(pdf_path)
    text_content = []
    image_paths = []
    
    for page_num in range(document.page_count):
        # Extract text
        text = extract_page_text(document, page_num)
        text_content.append(text)
        
        # Extract images
        images = extract_page_images(document, page_num)
        for img in images:
            path = save_image(img, image_output_dir, page_num)
            image_paths.append(path)
    
    return {
        "text": text_content,
        "images": image_paths
    }
```

### 7.2 Merging Process
```python
def merge_inspection_thermal(insp_data, therm_data, debug=False):
    areas = identify_areas(insp_data, therm_data)
    merged_findings = {}
    
    for area in areas:
        insp_issues = extract_area_issues(insp_data, area)
        therm_issues = extract_area_issues(therm_data, area)
        
        # Merge and deduplicate
        merged = merge_issues(insp_issues, therm_issues)
        conflicts = detect_conflicts(insp_issues, therm_issues)
        
        merged_findings[area] = {
            "issues": merged,
            "conflicts": conflicts,
            "missing_data": identify_missing_data(insp_issues, therm_issues)
        }
    
    return merged_findings
```

### 7.3 DDR Generation
```python
def generate_ddr_structured(merged_data, property_address, debug=False):
    prompt = format_prompt(merged_data, property_address)
    response = call_llm(prompt)
    structured_report = validate_and_parse_response(response)
    return structured_report
```

## 8. Output Format Example

```markdown
# Damp Diagnosis Report (DDR)

## 1. Property Issue Summary
...

## 2. Area-wise Observations
...

## 3. Probable Root Cause
...

## 4. Severity Assessment
...

## 5. Recommended Actions
...

## 6. Additional Notes
...

## 7. Missing or Unclear Information
...
```

## 9. Limitations

1. **OCR Quality Dependency**: Accuracy depends on input PDF quality
2. **Area Identification**: Relies on keyword matching which may miss variations
3. **Handwritten Content**: May not capture handwritten notes effectively
4. **LLM Hallucination**: Potential for plausible but incorrect information
5. **Image Mapping**: Heuristic-based approach may not always be accurate
6. **Manual Verification**: Requires human review for critical decisions

## 10. Future Improvements

1. **Advanced NLP Processing**: 
   - spaCy/HuggingFace transformers for entity recognition
   - Fine-tuned models for domain-specific understanding

2. **Computer Vision Integration**:
   - Automated image classification and analysis
   - Object detection for identifying issues in images

3. **Knowledge Graph Implementation**:
   - Relationship mapping between causes and solutions
   - Historical data correlation for better predictions

4. **Fine-tuned Domain Model**:
   - Custom LLM trained specifically on damp diagnosis reports
   - Improved accuracy for domain-specific terminology

5. **Enhanced Image Mapping**:
   - Computer vision for better image-to-section association
   - Automatic caption generation for images

6. **Real-time Collaboration**:
   - Web interface for team review and annotation
   - Version control for reports

7. **Automated Remediation Suggestions**:
   - Database-driven recommendation engine
   - Cost estimation for proposed solutions