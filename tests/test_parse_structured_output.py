import pytest
import sys

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluation.metrics import parse_structured_output

def test_parse_structured_output():
    # Test case with JSON in code block
    output1 = """Here is the analysis:
```json
{
  "events_detected": ["event1", "event2"],
  "timeline": ["event1", "event2"],
  "metrics": {"metric1": 0.95}
}
```
And here is some narrative explanation."""

    structured1, narrative1 = parse_structured_output(output1)
    assert structured1 is not None
    assert structured1['events_detected'] == ["event1", "event2"]
    assert "narrative explanation" in narrative1

    # Test case with JSON without code block
    output2 = """The detected events are as follows:
{
  "events_detected": ["eventA", "eventB"],
  "timeline": ["eventA", "eventB"],
  "metrics": {"metric1": 0.85}
}
This concludes the report."""
    structured2, narrative2 = parse_structured_output(output2)
    assert structured2 is not None
    assert structured2['events_detected'] == ["eventA", "eventB"]
    assert "concludes the report" in narrative2

    # Test case with no JSON
    output3 = "This is a free-form explanation without any structured data."
    structured3, narrative3 = parse_structured_output(output3)
    assert structured3 is None
    assert narrative3 == output3 

if __name__ == "__main__":
    pytest.main([__file__])