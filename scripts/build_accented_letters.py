import unicodedata


def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)


def get_accented_letters(letter):
    """returns the possible replacements for one letter (lower and upper case)"""
    letters = [letter.lower(), letter.upper()]
    accented_chars = []
    # This range contains Latin-1 Supplement Unicode block
    for i in range(0x00C0, 0x024F):
        char = chr(i)
        decomposed_char = unicodedata.normalize('NFD', char)
        if decomposed_char[0] in letters:
            accented_chars.append(char)
    return ''.join(letters) + ''.join(accented_chars)


def get_all_replacements():
  """returns an array containing all the possible replacements for all letters"""
  replacements = []
  for letter in char_range('a', 'z'):
    acc = get_accented_letters(letter)
    if acc:
      replacements.append(acc)
  return replacements


# generate python code for "globbing" a string
def generate_globber():
  replacements = ']",\n        "['.join(get_all_replacements())
  print(f'''
import re
def globalize_for_search(searchText):
  searchText = searchText.lower().replace("*", "[*]").replace("?", "[?]")
  replacements = [
        "[{replacements}]"]
  for replacement in replacements:
    searchText = re.sub(replacement, replacement, searchText)
  return searchText
''')


generate_globber()
