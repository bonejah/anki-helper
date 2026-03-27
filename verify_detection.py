from core.language import detect_language_safely
import sys

test_words = [
    "Mon oncle",
    "Une historie",
    "historie",
    "cher",
    "La Thailande",
    "un plat",
    "frère"
]

print("Starting Language Detection Verification...\n")
success = True

for word in test_words:
    detected = detect_language_safely(word)
    if detected == "fr":
        print(f"✅ '{word}' -> Detected correctly as French")
    else:
        print(f"❌ '{word}' -> Detected as {detected} (Expected: fr)")
        success = False

if success:
    print("\n🎉 All tests passed!")
    sys.exit(0)
else:
    print("\n⚠️ Some tests failed.")
    sys.exit(1)
