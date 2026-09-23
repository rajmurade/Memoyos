"""Streamlit AppTest smoke test for the full MemoryOS UI.

Run: python test_app.py

Checks that all five pages render without runtime exceptions. The LLM key is
temporarily removed so the test stays offline and deterministic.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # pragma: no cover - very old streamlit
    AppTest = None

PAGES = ["Ask MemoryOS", "Capture Memory", "Memory Library", "Incident Mode", "Knowledge Map"]


def main() -> None:
    if AppTest is None:
        print("SKIP: streamlit.testing.v1.AppTest not available")
        return

    previous_key = os.environ.get("LLM_API_KEY")
    os.environ.pop("LLM_API_KEY", None)
    try:
        at = AppTest.from_file("app.py", default_timeout=180)
        at.run()
        radios = at.sidebar.radio
        assert radios, "expected a sidebar radio navigation"
        print(f"Sidebar radio values: {list(radios[0].options)}")
        assert list(radios[0].options) == PAGES, f"unexpected pages: {list(radios[0].options)}"
        assert not at.exception, f"app raised on load: {at.exception}"

        for page in PAGES:
            radios[0].set_value(page)
            at.run()
            assert not at.exception, f"page {page!r} raised: {at.exception}"
            print(f"  [PASS] {page} renders without exceptions")

        print("\nPASS: all pages render via AppTest.")
    finally:
        if previous_key is not None:
            os.environ["LLM_API_KEY"] = previous_key
        else:
            os.environ.pop("LLM_API_KEY", None)


if __name__ == "__main__":
    main()