from django import template

register = template.Library()


@register.filter
def question_icon(question_type):
    icons = {
        "OT": "poll-open-text-question",
        "DT": "poll-date-time-question",
        "SC": "poll-choice-question",
        "MC": "poll-multiple-choice-question",
        "YN": "poll-yesno-question",
    }
    res = icons.get(question_type, "vote")
    # print(f"question icon for {question_type} = {res}")
    return res
