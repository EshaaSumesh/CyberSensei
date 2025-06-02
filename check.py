import google.generativeai as genai

# Authenticate with your API key
genai.api_key = 'AIzaSyDBUkjIXf1jhNdx2z6H2ZsJqDC1dpXPV68'  # Replace with your actual API key
try:
    # Send a simple request to the API to check if everything is set up properly
    response = genai.generate_content(prompt="Hello, check if this works!")
    
    # If the response is successful, print a success message
    print("Authentication successful! You are connected to Google Gemini.")
    print("Response from API:", response)
except Exception as e:
    print(f"Error occurred: {e}")