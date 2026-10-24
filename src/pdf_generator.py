import typst
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_pdf(typst_content: str, output_path: str):
    """
    Compiles Typst content to a PDF file.
    
    Args:
        typst_content (str): The Typst code.
        output_path (str): The absolute path to save the PDF.
    """
    logger.info(f"Compiling PDF to {output_path}...")
    
    try:
        # We might need to write to a temporary file first if the compiler needs a file context
        # But python-typst usually handles strings or files.
        # Let's write the tailored content to a .typ file next to the output pdf first.
        
        typ_path = Path(output_path).with_suffix('.typ')
        with open(typ_path, 'w', encoding='utf-8') as f:
            f.write(typst_content)
            
        # Compile
        typst.compile(typ_path, output=output_path)
        
        logger.info("PDF compilation successful.")
        
    except Exception as e:
        logger.error(f"Error compiling PDF: {e}")
        raise

if __name__ == "__main__":
    # Test
    pass
