from DrissionPage import ChromiumPage, ChromiumOptions

class Chromium:
    def __init__(self, api_key: str):
        co = ChromiumOptions()
        co.arguments.append('--blink-settings=imagesEnabled=false')
        page = ChromiumPage(addr_or_opts=co)
        page.get("https://weav3r.dev/login")
        page.ele("#apiKey").input(api_key)
        page.ele("#rememberMe").click()
        page.ele("#agreedToTerms").click()
        page.ele("tag:button@type=submit").click()
        page.wait(1)
        self.Page = page

    def refresh(self, item_id: int):
        self.Page.get(f"https://weav3r.dev/item/{item_id}")
        elems = self.Page.ele("tag:tbody").children()
        if len(elems) > 0:
            self.Page.wait(1.5)
            elems[0].ele("tag:button").click()

    def quit(self):
        self.Page.quit()
