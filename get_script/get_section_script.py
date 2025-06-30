# this is just playwright code


def get_section_script(page, title=None, code=None, section_number=None):
    """ generate script for a specific section of the outline using ChatGPT

    Args:
        page (_type_) : Playwright page object to interact with the browser.
        title (_type_, optional): Title of the section. Defaults to None.
        code (_type_, optional): Code snippet for the section. Defaults to None.
    """
    # args check make sure nothing is None
    if title is None:
        raise ValueError("Title must be provided")
    if code is None:
        raise ValueError("Code must be provided")
    if section_number is None:
        raise ValueError("Section number must be provided")
    
    print("success: section number: ", section_number)
    return True  # Placeholder return value to indicate success