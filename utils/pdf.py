import os


def generate_pdf(html_string, base_url=None):
    # imported inside the function so the app still runs without Playwright
    from playwright.sync_api import sync_playwright

    # the HTML is loaded from a string, so a <link> to /static/... can't be
    # fetched. We read resume.css from disk and inject it instead.
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "static", "css", "resume.css"
    )
    with open(css_path, encoding="utf-8") as f:
        css = f.read()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_string)
        page.add_style_tag(content=css)
        pdf = page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()

    return pdf
