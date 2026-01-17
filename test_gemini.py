# """
# Test Gemini API integration
# """

# from engine.llms import gemini_response
# import os

# # Test with mock (no API key needed)
# print("="*70)
# print("TEST 1: Mock Response (No API Key)")
# print("="*70)

# response = gemini_response("What is artificial intelligence?", {
#     'model': 'gemini-pro',
#     'temperature': 0.7,
#     'max_tokens': 1000
# })

# print(f"\nPrompt: What is artificial intelligence?")
# print(f"Response: {response}\n")

# # Test with real API key (if available)
# print("="*70)
# print("TEST 2: Real Gemini API (If API Key is Set)")
# print("="*70)

# if os.getenv("GEMINI_API_KEY"):
#     print("\n✓ GEMINI_API_KEY found in environment")
#     print("Calling Gemini API...\n")
    
#     response = gemini_response(
#         "Explain quantum computing in one sentence.",
#         {
#             'model': 'gemini-pro',
#             'temperature': 0.7,
#             'max_tokens': 100
#         }
#     )
    
#     print(f"Prompt: Explain quantum computing in one sentence.")
#     print(f"Response: {response}")
# else:
#     print("\n⚠ GEMINI_API_KEY not found in environment")
#     print("To test with real Gemini API:")
#     print("1. Get API key from: https://makersuite.google.com/app/apikey")
#     print("2. Add to .env file: GEMINI_API_KEY=your_key_here")
#     print("3. Run: pip install google-generativeai")

# print("\n" + "="*70)





from engine.llms import gemini_response

response = gemini_response(
    "What is AI?",
    {'model': 'gemini-2.5-flash', 'temperature': 0.7}
)

print("Gemini Response:")
print(response)
