import re
import urllib.parse
from collections import defaultdict
from typing import List, Optional

import markdown2
from fpdf import FPDF
from fpdf.fonts import FontFace

try:
    from tabulate import tabulate
except ImportError:

    def tabulate(*args, **kwargs):
        raise ImportError("Please install tabulate to use the TableBlock")


from robusta.core.reporting import (
    BaseBlock,
    DividerBlock,
    FileBlock,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    ScanReportBlock,
    TableBlock,
)


class Transformer:
    @staticmethod
    def apply_length_limit(msg: str, max_length: int, truncator: Optional[str] = None) -> str:
        """
        Method that crops the string if it is bigger than max_length provided.
        Args:
            msg: The string that needs to be truncated.
            max_length: Max length of the string allowed
            truncator: truncator string that will be appended, if max length is exceeded.

        Examples:

            >>> print(Transformer.apply_length_limit('1234567890', 9))
            123456...

            >>> print(Transformer.apply_length_limit('1234567890', 9, "."))
            12345678.

        Returns:
            Croped string with truncator appended at the end if length is exceeded.
            The original string otherwise

        """
        if len(msg) <= max_length:
            return msg
        truncator = truncator or "..."
        return msg[: max_length - len(truncator)] + truncator

    @staticmethod
    def to_markdown_diff(block: KubernetesDiffBlock, use_emoji_sign: bool = False) -> List[ListBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        divider = ":arrow_right:" if use_emoji_sign else "==>"
        _blocks = []
        _blocks.extend(ListBlock([f"*{d.formatted_path}*: {d.other_value} {divider} {d.value}" for d in block.diffs]))

        return _blocks

    @staticmethod
    def get_markdown_links(markdown_data: str) -> List[str]:
        regex = "<.*?\\|.*?>"
        matches = re.findall(regex, markdown_data)
        links = []
        if matches:
            links = [match for match in matches if len(match) > 1]  # filter out illegal matches
        return links

    @staticmethod
    def to_github_markdown(markdown_data: str, add_angular_brackets: bool = True) -> str:
        """Transform all occurrences of slack markdown, <URL|LINK TEXT>, to github markdown [LINK TEXT](URL)."""
        # some markdown parsers doesn't support angular brackets on links
        OPENING_ANGULAR = "<" if add_angular_brackets else ""
        CLOSING_ANGULAR = ">" if add_angular_brackets else ""
        matches = Transformer.get_markdown_links(markdown_data)
        for match in matches:
            # take only the data between the first '<' and last '>'
            splits = match[1:-1].split("|")
            if len(splits) == 2:  # don't replace unexpected strings
                parsed_url = urllib.parse.urlparse(splits[0])
                parsed_url = parsed_url._replace(path=urllib.parse.quote_plus(parsed_url.path, safe="/"))
                replacement = f"[{splits[1]}]({OPENING_ANGULAR}{parsed_url.geturl()}{CLOSING_ANGULAR})"
                markdown_data = markdown_data.replace(match, replacement)
        return re.sub(r"\*([^\*]*)\*", r"**\1**", markdown_data)

    @classmethod
    def __markdown_to_html(cls, mrkdwn_text: str) -> str:
        # replace links: from <http://url|name> to <a href="url">name</a>
        mrkdwn_links = re.findall(r"<[^\\|]*\|[^\>]*>", mrkdwn_text)
        for link in mrkdwn_links:
            link_content = link[1:-1]
            link_parts = link_content.split("|")
            mrkdwn_text = mrkdwn_text.replace(link, f'<a href="{link_parts[0]}">{link_parts[1]}</a>')

        # replace slack markdown bold: from *bold text* to <b>bold text<b>  (markdown2 converts this to italic)
        mrkdwn_text = re.sub(r"\*([^\*]*)\*", r"<b>\1</b>", mrkdwn_text)

        # Note - markdown2 should be used after slack links already converted, otherwise it's getting corrupted!
        # Convert other markdown content
        return markdown2.markdown(mrkdwn_text)

    @classmethod
    def to_html(cls, blocks: List[BaseBlock]) -> str:
        lines = []
        for block in blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"{cls.__markdown_to_html(block.text)}")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(
                        cls.__markdown_to_html(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
                    )
            elif isinstance(block, HeaderBlock):
                lines.append(f"<strong>{block.text}</strong>")
            elif isinstance(block, ListBlock):
                lines.extend(cls.__markdown_to_html(block.to_markdown().text))
            elif isinstance(block, TableBlock):
                if block.table_name:
                    lines.append(cls.__markdown_to_html(block.table_name))
                lines.append(tabulate(block.render_rows(), headers=block.headers, tablefmt="html").replace("\n", ""))
        return "\n".join(lines)

    @classmethod
    def to_standard_markdown(cls, blocks: List[BaseBlock]) -> str:
        lines = []
        for block in blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"{cls.to_github_markdown(block.text, False)}")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(f"**{'.'.join(diff.path)}**: {diff.other_value} ==> {diff.value}")
            elif isinstance(block, HeaderBlock):
                lines.append(f"**{block.text}**")
            elif isinstance(block, ListBlock):
                lines.extend(cls.to_github_markdown(block.to_markdown().text, False))
            elif isinstance(block, TableBlock):
                if block.table_name:
                    lines.append(cls.to_github_markdown(block.table_name, False))
                rendered_rows = block.render_rows()
                lines.append(tabulate(rendered_rows, headers=block.headers, tablefmt="presto"))
        return "\n".join(lines)

    @staticmethod
    def tableblock_to_fileblocks(blocks: List[BaseBlock], column_limit: int) -> List[FileBlock]:
        file_blocks: List[FileBlock] = []
        for table_block in [b for b in blocks if isinstance(b, TableBlock)]:
            if len(table_block.headers) >= column_limit:
                table_name = table_block.table_name if table_block.table_name else "data"
                table_content = table_block.to_table_string(table_max_width=250)  # bigger max width for file
                file_blocks.append(FileBlock(f"{table_name}.txt", bytes(table_content, "utf-8")))
                blocks.remove(table_block)

        return file_blocks

    @staticmethod
    def scanReportBlock_to_fileblock(block: BaseBlock) -> BaseBlock:

        if not isinstance(block, ScanReportBlock):
            return block

        accent_color = (140, 249, 209)
        headers_color = (63, 63, 63)
        table_color = (207, 215, 216)

        def set_normal_test_style(pdf: FPDF):
            pdf.set_font("", "", 8)
            pdf.set_text_color(0, 0, 0)

        def write_report_header(title: str, end_time, score: int, grade: str):
            pdf.cell(pdf.w * 0.7, 10, f"**{title}** {end_time.strftime('%b %d, %y %X')}", border=0, markdown=True)
            if int(score) >= 0:
                pdf.cell(pdf.w * 0.3, 10, f"**{grade}** {score}", border=0, markdown=True)

            pdf.ln(20)

        def write_section_header(pdf: FPDF, header: str):
            if pdf.will_page_break(50):
                pdf.add_page()

            pdf.ln(12)
            pdf.set_font("", "B", 12)
            pdf.set_text_color(headers_color)
            pdf.cell(txt=header, border=0)
            pdf.ln(12)

        def write_config(pdf: FPDF, config: str):
            pdf.set_text_color(accent_color)
            pdf.cell(txt="config", border=0)
            pdf.ln(12)
            set_normal_test_style(pdf)
            pdf.multi_cell(w=0, txt=config, border=0)

        def write_table(pdf: FPDF, rows: list[list[str]]):
            pdf.set_draw_color(table_color)
            set_normal_test_style(pdf)
            with pdf.table(
                borders_layout="INTERNAL",
                rows=rows,
                headings_style=FontFace(color=(headers_color)),
                col_widths=(10, 25, 25, 65),
                markdown=True,
                line_height=1.5 * pdf.font_size,
            ):
                pass

        scan: ScanReportBlock = block
        pdf = FPDF(orientation="landscape", format="A4")
        pdf.add_page()
        pdf.set_font("courier", "", 18)
        pdf.set_line_width(0.1)
        pdf.c_margin = 2  # create default cell margin to add table "padding"

        title = f"{scan.type.capitalize()} report"
        write_report_header(title, scan.end_time, scan.score, scan.grade())
        write_config(pdf, scan.config)

        sections: dict[str, dict[str, List]] = defaultdict(lambda: defaultdict(list))
        for item in scan.results:
            sections[item.kind][f"{item.name}/{item.namespace}"].append(item)

        for kind, grouped_issues in sections.items():

            rows = [["Priority", "Name", "Namespace", "Issues"]]
            for group, scanRes in grouped_issues.items():
                n, ns = group.split("/", 1)
                issue_txt = ""
                max_priority: int = 0
                for res in sorted(scanRes, key=lambda x: len(x.container)):
                    issue_txt += scan.pdf_scan_row_content_format(row=res)
                    max_priority = max(max_priority, res.priority)
                    rows.append([scan.pdf_scan_row_priority_format(max_priority), n, ns, issue_txt])

            write_section_header(pdf, kind)
            write_table(pdf, rows)

        return FileBlock(f"{title}.pdf", pdf.output("", "S"))
