import streamlit as st
import os
import sys
import tempfile
import argparse
from pathlib import Path

# Add current directory to path so we can import book_maker modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from book_maker.loader import BOOK_LOADER_DICT
from book_maker.translator import MODEL_DICT
from book_maker.utils import LANGUAGES, TO_LANGUAGE_CODE
from book_maker.translator.gemini_translator import GEMINIPRO_MODEL_LIST, GEMINIFLASH_MODEL_LIST

# ... imports remain same
import time

# Create a mapping for display
LANGUAGE_DISPLAY_MAP = {
    code: f"{code} ({name})" for code, name in LANGUAGES.items()
}
# Custom overrides
LANGUAGE_DISPLAY_MAP["zh-hans"] = "zh-hans (简体中文)"
LANGUAGE_DISPLAY_MAP["zh-hant"] = "zh-hant (繁體中文)"
LANGUAGE_DISPLAY_MAP["ja"] = "ja (日本語)"
LANGUAGE_DISPLAY_MAP["ko"] = "ko (한국어)"

# Reverse map
DISPLAY_TO_CODE = {v: k for k, v in LANGUAGE_DISPLAY_MAP.items()}

# Priority languages to show at the top
PRIORITY_LANGUAGES = ["zh-hans", "zh-hant", "ja", "ko", "en"]
# Priority languages to show at the top (zh-hant first)
PRIORITY_LANGUAGES = ["zh-hant", "zh-hans", "ja", "ko", "en"]

def get_sorted_display_options():
    all_codes = list(LANGUAGE_DISPLAY_MAP.keys())
    # Remove priority codes from general list to avoid duplicates when appending
    remaining_codes = sorted([c for c in all_codes if c not in PRIORITY_LANGUAGES])
    
    sorted_codes = [c for c in PRIORITY_LANGUAGES if c in LANGUAGE_DISPLAY_MAP] + remaining_codes
    return [LANGUAGE_DISPLAY_MAP[c] for c in sorted_codes]

# ... imports
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup


def extract_preview(file_path, suffix, limit=2000):
    text = ""
    success = True
    try:
        if suffix == ".epub":
            book = epub.read_epub(file_path)
            # Try to get text from the first few documents
            count = 0
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                # crude text extraction
                try:
                    content = item.get_content()
                    soup = BeautifulSoup(content, 'html.parser')
                    text += soup.get_text() + "\n"
                    count += len(text)
                    if count > limit:
                        break
                except Exception:
                    continue
            if not text.strip():
                 text = "Could not extract text from EPUB."
                 success = False

        else:
            # Fallback for text files with different encodings
            raw_data = open(file_path, "rb").read(limit)
            try:
                text = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = raw_data.decode("gb18030") # Common for chinese
                except UnicodeDecodeError:
                    text = raw_data.decode("latin-1", errors="ignore")
                    
    except Exception as e:
        return f"Error reading file preview: {e}", False
        
    return text[:limit], success


def main():
    st.set_page_config(page_title="Bilingual Book Maker", page_icon="📚", layout="wide")
    
    if 'suggestions' not in st.session_state:
        st.session_state.suggestions = []
        
    # Removed custom_prompt state initialization

    st.title("📚 Bilingual Book Maker AI")
    st.markdown("Translate EPUB/TXT/SRT files using various AI models (ChatGPT, Gemini, Claude, etc.)")

    # Sidebar for API Configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # Model Selection
        model_type = st.selectbox(
            "Select Translation Model Type",
            ["gemini", "openai", "claude", "caiyun", "deepl", "groq", "xai", "qwen", "google"]
        )
        
        api_key = st.text_input(f"{model_type.upper()} API Key", type="password")
        
        # Specific Model selection for Gemini/OpenAI etc
        specific_model = None
        if model_type == "gemini":
            gemini_models = GEMINIPRO_MODEL_LIST + GEMINIFLASH_MODEL_LIST
            specific_model = st.selectbox("Select Gemini Model", gemini_models)
        elif model_type == "openai":
            specific_model = st.selectbox("Select OpenAI Model", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview"])
        elif model_type == "claude":
            specific_model = st.selectbox("Select Claude Model", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"])
            
        base_url = st.text_input("API Base URL (Optional)", help="Override default API endpoint")

    # Main Content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. 📂 File Selection")
        uploaded_file = st.file_uploader("Upload your file", type=["epub", "txt", "srt", "html"])
        
    with col2:
        st.subheader("2. ⚙️ Translation Options")
        
        # Language Selection with prioritized sorting
        display_options = get_sorted_display_options()
        
        selected_display = st.selectbox(
            "Target Language",
            display_options,
            index=0 
        )
        target_lang_code = DISPLAY_TO_CODE[selected_display]
        st.caption(f"Selected Language Code: {target_lang_code}")
        
        mode = st.radio("Translation Mode", ["Bilingual (Original + Translated)", "Single Translate (Translated only)"])
        single_translate = mode == "Single Translate (Translated only)"
        

        # Translation Limit / Range
        st.write("Translation Range:")
        limit_mode = st.radio("Limit Type", ["Full Book", "Custom (Paragraphs)", "Percentage (0-100%)"], horizontal=True, label_visibility="collapsed")
        
        test_num = 999999
        is_test = False
        
        if limit_mode == "Custom (Paragraphs)":
            test_num = st.number_input("Number of paragraphs to translate", min_value=1, value=10)
            is_test = True
        elif limit_mode == "Percentage (0-100%)":
            st.info("Percentage mode is currently approximated using paragraph counts for performance.")
            test_num = st.number_input("Approximate Number of Paragraphs (representing %)", min_value=1, value=50)
            is_test = True

        resume = st.checkbox("Resume Translation (from last progress)", value=False, help="Use this if a previous translation failed or was interrupted.")


        # Advanced Options - Simplified (No Prompt)
        with st.expander("🛠️ Advanced Configuration", expanded=False):
            # Only Translation Style remains
            batch_size = 10 
            
            translation_style = st.text_input("Translation Style (CSS)", help="e.g. 'color: #808080; font-style: italic;' (for EPUB)")

        # State management for Button
        if "translating" not in st.session_state:
            st.session_state.translating = False
            
        def on_click_translate():
            st.session_state.translating = True
        
        req_key = True
        if model_type == 'google':
             req_key = False
             
        disabled_btn = st.session_state.translating or not uploaded_file
        if req_key and not api_key:
             disabled_btn = True

        if st.button("🚀 Start Translation", type="primary", disabled=disabled_btn, on_click=on_click_translate):
            try:
                result_path = process_translation(
                    uploaded_file, 
                    model_type, 
                    specific_model, 
                    api_key, 
                    base_url, 
                    target_lang_code, 
                    single_translate, 
                    is_test,
                    test_num, 
                    None, # Passing None for prompt_template
                    batch_size,
                    translation_style,
                    resume
                )
                if result_path and os.path.exists(result_path):
                     st.session_state.translation_result = result_path
                     st.success("Translation Complete! 🎉")
            except Exception as e:
                st.error(f"Translation failed: {str(e)}")
            finally:
                st.session_state.translating = False
                # Do NOT rerun here immediately if we want to show success in this frame?
                # Actually, if we don't rerun, the "translating" state remains True in the UI until next interaction?
                # No, we set it to False.
                # If we don't rerun, the button stays 'disabled' visually? 
                # Streamlit button `disabled` state updates on rerun.
                # If we don't rerun, the button might look stuck.
                # BUT if we rerun, `st.button` becomes False.
                # We saved result to `st.session_state.translation_result`.
                # So even if we rerun, we can render the download button from session state!
                st.rerun()

        # Persistent Display of Download Button
        if "translation_result" in st.session_state and os.path.exists(st.session_state.translation_result):
            st.success("Translation Ready!")
            result_path = st.session_state.translation_result
            file_name = f"translated_{Path(result_path).name}"
             # Determine original name logic if needed, but simple is fine
             
            with open(result_path, "rb") as file:
                st.download_button(
                    label="Download Translated Book",
                    data=file,
                    file_name=os.path.basename(result_path),
                    mime="application/octet-stream"
                )

# ... (Rest of TqdmPatcher and imports ...)


# Mock Tqdm to update Streamlit progress bar
class StreamlitTqdm:
    def __init__(self, iterable=None, total=None, *args, **kwargs):
        self.iterable = iterable
        self.total = total
        self.current = 0
        self.bar = st.progress(0, text="Initializing...")
        
    def __iter__(self):
        for obj in self.iterable:
            yield obj
            self.update()
            
    def update(self, n=1):
        self.current += n
        percentage = 0
        if self.total:
            percentage = min(self.current / self.total, 1.0)
            self.bar.progress(percentage, text=f"Progress: {int(percentage*100)}% ({self.current}/{self.total})")
        else:
            # If total is unknown, we can't effectively progress bar. Just show text?
            # Or use a spinner logic?
            self.bar.progress(0, text=f"Processed {self.current} items (Total unknown)")

    def close(self):
        self.bar.empty()

# Context manager to patch tqdm
class TqdmPatcher:
    def __enter__(self):
        self.original_tqdm = sys.modules['tqdm'].tqdm
        sys.modules['tqdm'].tqdm = StreamlitTqdm
        
        self.patched_modules = []
        targets = [
            'book_maker.loader.epub_loader',
            'book_maker.loader.txt_loader',
            'book_maker.loader.srt_loader', 
        ]
        
        for name in targets:
            if name in sys.modules:
                mod = sys.modules[name]
                if hasattr(mod, 'tqdm'):
                    self.patched_modules.append((mod, getattr(mod, 'tqdm')))
                    setattr(mod, 'tqdm', StreamlitTqdm)
        
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.modules['tqdm'].tqdm = self.original_tqdm
        for mod, original in self.patched_modules:
            setattr(mod, 'tqdm', original)

from tqdm import tqdm
import sys
import json


def process_translation(uploaded_file, model_type, specific_model, api_key, base_url, target_lang, single_translate, is_test, test_num, prompt_template, batch_size, translation_style, resume):
    if not uploaded_file:
        return None

    # Create a temporary file to save the uploaded content
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    st.info(f"Processing file: {uploaded_file.name}...")
    
    try:
        # Resolve Language Code (handled by caller now)
        language_code = target_lang
        
        translate_model_cls = MODEL_DICT.get(model_type)
        if not translate_model_cls:
            st.error("Unsupported model type")
            return None

        book_type = suffix.lstrip('.')
        book_loader_cls = BOOK_LOADER_DICT.get(book_type)
        if not book_loader_cls:
            st.error(f"Unsupported file type: {suffix}")
            return None
        
        # No prompt parsing, just pass None
        prompt_config = None
        
        loader = book_loader_cls(
            tmp_file_path,
            translate_model_cls,
            api_key,
            resume=resume,
            language=language_code,
            model_api_base=base_url if base_url else None,
            is_test=is_test,
            test_num=test_num, 
            single_translate=single_translate,
            context_flag=False,
            prompt_config=prompt_config
        )
        
        # Apply advanced options
        if batch_size:
            loader.batch_size = batch_size
        if translation_style:
            loader.translation_style = translation_style

        if model_type == "gemini" and specific_model:
            if hasattr(loader.translate_model, "set_models"):
                loader.translate_model.set_models([specific_model])
                
        if model_type == "openai" and specific_model:
             if hasattr(loader.translate_model, "set_model_list"):
                 loader.translate_model.set_model_list([specific_model])
            
        
        # Run translation with patched Tqdm
        with TqdmPatcher():
            loader.make_bilingual_book()
            
        
        output_path = tmp_file_path.replace(suffix, f"_bilingual{suffix}")
        
        if os.path.exists(output_path):
             return output_path
        else:
            st.warning(f"Could not automatically locate output file at {output_path}. Please check logs.")
            return None

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
        return None
    finally:
        pass

if __name__ == "__main__":
    main()
