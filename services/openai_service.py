# services/openai_service.py

from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_bot_response(prompt: str) -> str:
   

    system_prompt = """
You are a friendly and professional insurance agent named 'Whylek_insurance'. 
You help users complete their car insurance purchase process. 
Always respond in English.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def generate_insurance_policy(user_data: dict) -> str:
    """
    Генерує страховий поліс на основі даних користувача.
    """

    # Витягуємо дані з passport
    passport = user_data.get("passport", {})
    surname = passport.get("surname", "SURNAME")
    given_names = passport.get("given_names", ["Name"])
    first_name = given_names[0] if len(given_names) > 0 else "Name"
    full_name = f"{first_name} {surname}"

    # Дата народження
    dob = passport.get("birth_date", "01.01.1990")

    # Дані про авто
    vehicle = user_data.get("vehicle", {})
    vin = vehicle.get("vin", "VIN1234567890XYZ")
    license_plate = vehicle.get("license_plate", "ABC123")

    prompt = f"""
You are a professional legal writer. Generate a clear, formal, and professional **Car Insurance Policy Document** using the information provided below. The document should resemble a real policy and include standard sections such as:

1. **Policy Summary**
2. **Policy Holder Details**
3. **Vehicle Information**
4. **Coverage Details** (you may use standard placeholders)
5. **Terms and Conditions** (brief, formal)
6. **Claims Process**
7. **Contact Information**

Use clear headings and maintain a professional tone throughout. Do not invent specific personal details beyond what is provided.

### Policy Holder Information:
- **Full Name:** {full_name}
- **Date of Birth:** {dob}
- **License Plate Number:** {license_plate}
- **Vehicle Identification Number (VIN):** {vin}

**Contact Information:**
+380679342672  
support@insurancecompany.com  
221B Baker Street, London  

**[Whylek_insurance]**  
*Safe travels with peace of mind.*
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that generates realistic insurance policies."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content