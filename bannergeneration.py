from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

from supabasecode import upload_banner, save_plan
import traceback

#Google genai
client = genai.Client(api_key = st.secrets.get("GOOGLE_API_KEY"))

def try_generate_banner(super_goal: str) -> bytes:
    prompt = f"""
    Please help me design a 1536:512 landscape dashboard banner for this super goal: {super_goal}
    If the original super goal text is has more than 12 words or has complex wording:
    - adapt to to a banner title by removing excessive details
    - keep the keywords and a key number
    - focus on practical action verbs (eg. reach, learn, make) ignore common english sentence structure

    The optimized super goal title is placed in the top-left overlay in a clean, bold title font.
    The main element of the banner is the cartoon:
    - The theme of the goal should illustrated through a primary subject
    - The story telling is complete through lighthearted and humurous states and actions
    - ONLY if suitable, humour can be convyed with exaggerated body proportions, especially through contrast with multiple characters
    
    Specific artistic choice for the cartoon:
    - Simple and bold look for characters, settings, and props
    - Preferably consistent line style: Thick, black outlines with rounded ends; no sketchy or variable stroke.
    - No background wash. Simple Palette: Most lines are black on white; 1‑2 selective colours fills only as accent for goal‑defining items (eg. youtube plaque, computer)
    - Tweak the style of the banner to align more with the two reference images provided: NAMELY the character style, contrasting and humurous details, and detailing
    """

    # Load reference images
    img1 = Image.open("reference.png")
    img2 = Image.open("reference2.png")

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=[prompt, img1],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        )
    )

    # Extract and return final image bytes
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    raise RuntimeError("Gemini returned no image")

def async_generate_and_upload(super_goal: str, username: str) -> str:
    print("streamlit CODE not allowed in this image generation process")

    data = try_generate_banner(super_goal)       # may raise
    url  = upload_banner(username, data)         # may raise
    return url