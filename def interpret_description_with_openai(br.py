def interpret_description_with_openai(brand_name, description):
    prompt = f"""
    The brand "{brand_name}" specializes in the following: {description}.
    For each product category, provide the following details in the format:
    "Product_category", "Tariff Applied", "Country", "Comments related to the tariffs".
    Ensure the response is structured as a table with one row per product category.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts product categories and retrieves tariff information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )
    print("Raw OpenAI Response:", response)  # Log the raw response

    # Parse the response
    results = response['choices'][0]['message']['content'].strip().split("\n")
    structured_data = []
    for result in results:
        parts = result.split(",")  # Split by comma
        if len(parts) == 4:
            structured_data.append({
                "product": parts[0].strip(),
                "tariff": parts[1].strip(),
                "country": parts[2].strip(),
                "comments": parts[3].strip()
            })
    return structured_data

test_brand = "Outdoor Gear Co."
test_description = "This brand specializes in outdoor gear, including tents, backpacks, and hiking boots."
print(interpret_description_with_openai(test_brand, test_description))