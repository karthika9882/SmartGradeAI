from app.services.evaluator import baseline_evaluation

def test_empty_answer_gets_zero():
    result = baseline_evaluation("", "reference answer", [], 5)
    assert result["recommended_marks"] == 0

def test_marks_are_bounded():
    result = baseline_evaluation("Plants use sunlight and chlorophyll to make glucose and release oxygen.",
        "Photosynthesis uses sunlight chlorophyll water carbon dioxide to produce glucose oxygen.",
        [{"criterion":"Sunlight","keywords":["sunlight"],"marks":2},
         {"criterion":"Oxygen","keywords":["oxygen"],"marks":2}], 4)
    assert 0 <= result["recommended_marks"] <= 4
