from app.mbti.mbti_result import MBTIResult


def test_process_mbti_result():
    result = MBTIResult()
    test_answers = {
        "E/I": ["E", "E", "I"],
        "S/N": ["S", "S", "S"],
        "T/F": ["T", "F", "T"],
        "J/P": ["J", "J", "J"],
    }
    mbti_type = result.process_result(test_answers)
    assert len(mbti_type) == 4
