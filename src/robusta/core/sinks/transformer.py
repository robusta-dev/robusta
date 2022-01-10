import re


class Transformer:
    @staticmethod
    def to_github_markdown(markdown_data: str) -> str:
        """Transform all occurrences of slack markdown, <URL|LINK TEXT>, to github markdown [LINK TEXT](URL)."""
        regex = "<.*?\\|.*?>"
        matches = re.findall(regex, markdown_data)
        if matches:
            matches = [
                match for match in matches if len(match) > 1
            ]  # filter out illegal matches
            for match in matches:
                # take only the data between the first '<' and last '>'
                splits = match[1:-1].split("|")
                if len(splits) == 2:  # don't replace unexpected strings
                    replacement = f"[{splits[1]}](<{splits[0]}>)"
                    markdown_data = markdown_data.replace(match, replacement)
        return markdown_data
