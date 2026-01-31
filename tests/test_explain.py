import unittest

from spoon.validators import ExplainValidationError, validate_explain_payload


class TestExplainValidation(unittest.TestCase):
    def test_valid_payload(self) -> None:
        payload = {
            "decision": "Do something",
            "rationale": ["Because"],
            "assumptions": ["Assume A"],
            "risks": [
                {"risk": "Risk", "severity": "LOW", "mitigation": "Mitigate"}
            ],
            "alternatives": [{"option": "Alt", "why_not": "Slower"}],
        }
        validate_explain_payload(payload)

    def test_missing_rationale(self) -> None:
        payload = {
            "decision": "Do something",
            "assumptions": ["Assume A"],
            "risks": [
                {"risk": "Risk", "severity": "LOW", "mitigation": "Mitigate"}
            ],
            "alternatives": [{"option": "Alt", "why_not": "Slower"}],
        }
        with self.assertRaises(ExplainValidationError):
            validate_explain_payload(payload)


if __name__ == "__main__":
    unittest.main()
