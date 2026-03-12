import os
import threading
import traceback
from src.api.setup_api import logger
from src.utils.app_state import app_state
from src.interfaces.interface import build_interface
from src.api.endpoints import APIEndpoints  # your Flask API

def background_initialize():
    """Initialize heavy stuff without blocking the main server port."""
    try:
        logger.info("Initializing app_state in background…")
        ok = app_state.initialize()
        if ok:
            logger.info("Initialization complete.")
        else:
            logger.error("Initialization failed (initialize() returned False).")
    except Exception:
        logger.error("Initialization crashed:\n%s", traceback.format_exc())

def start_gradio():
    """Start Gradio interface on a separate port."""
    try:
        iface = build_interface()
        logger.info("Launching Gradio UI on :7861")
        # Disable auto_open so it doesn't hang in server env
        iface.launch(
            server_name="0.0.0.0",
            server_port=7861,   # Different port than Render's $PORT
            share=False,
            debug=False,
            show_error=True,
            quiet=True,
            prevent_thread_lock=True
        )
    except Exception:
        logger.error("Gradio crashed:\n%s", traceback.format_exc())

if __name__ == "__main__":
    logger.info("Starting Document Q&A Assistant (Render)")

    # Initialize required components before starting servers.
    if not app_state.initialize():
        logger.error("Application initialization failed. Exiting.")
        raise SystemExit(1)

    # Start Gradio in background on another port
    threading.Thread(target=start_gradio, daemon=True).start()

    # Start Flask API on Render's assigned PORT
    port = int(os.environ.get("PORT", "5000"))
    api = APIEndpoints(
        qa_chain=app_state.qa_chain,
        cache_manager=app_state.cache_manager,
        security_manager=app_state.security_manager
    )
    logger.info(f"Starting Flask API on :{port}")
    api.run(host="0.0.0.0", port=port)
