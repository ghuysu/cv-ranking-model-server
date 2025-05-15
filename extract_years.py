import re

def extract_year_range(experience_str):
    if not isinstance(experience_str, str):
        return 0, 0

    experience_str = experience_str.lower()
    numbers = list(map(int, re.findall(r'\d+', experience_str)))

    if len(numbers) >= 2:
        return numbers[0]*12, numbers[1]*12
    elif "+" in experience_str or "at least" in experience_str or "minimum" in experience_str or "more than" in experience_str:
        return numbers[0]*12, float('inf')
    elif "up to" in experience_str or "less than" in experience_str:
        return 0, numbers[0]*12
    elif len(numbers) == 1:
        return numbers[0]*12, numbers[0]*12

    return 0, 0

def extract_year_resume(experience_str):
    if not isinstance(experience_str, str):
        return 0, 0

    experience_str = experience_str.lower()
    numbers = list(map(int, re.findall(r'\d+', experience_str)))
    if len(numbers) == 0: return 0
    if len(numbers) == 1 :
        return numbers[0]*12
    return numbers[0]*12 + numbers[1]
