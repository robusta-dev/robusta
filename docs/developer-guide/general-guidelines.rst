Coding Conventions and General Developer Guidelines
###################################################

1. Use pydantic.BaseModel instead of Python dataclasses when possible. Pydantic performs datavalidation whereas Python
dataclasses just reduce boilerplate code like defining __init__()
