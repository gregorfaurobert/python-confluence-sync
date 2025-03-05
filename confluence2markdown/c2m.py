# imports
import argparse
import shutil
import os
# formerly used python's HTML parser, changed to bs4:
# from HTMLParser import HTMLParser
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from pathlib import Path

# flags
rendering_html = False
indent = -1
li_break = False
li_for_ul_only = False # see convert_li
list_nr = 0

# linebreaks
md_br = "\n"
md_dbr = "\n\n"
html_br = "<br/>"
html_dbr = "<br/><br/>"
def linebreak():
    if rendering_html:
        return html_br
    else:
        return md_br

# global vars
title = "none"

# convert the passed html-tag. Delegates to convert-* functions depending on tag
def convert_html_tag(tag):
    if tag is None:
        return ""

    # info about this tag:
    tag_info = ("convert_html_tag: type="+(str(type(tag))) + ", classname="+tag.__class__.__name__)
    try:
         if (not tag.__class__ == NavigableString) and (tag.name is not None):
            tag_info += (", name="+tag.name)
    except:
        pass
    # print(tag_info) 
    
    if tag.__class__ == NavigableString:
        return tag

    # Handle Confluence-specific tags
    if tag.name == "ac:task-list":
        return convert_task_list(tag)
    
    if tag.name == "ac:structured-macro":
        return convert_structured_macro(tag)
    
    if tag.name == "ac:image":
        return convert_img(tag)
    
    # Handle standard HTML tags
    if tag.name == "div":
        return convert_div(tag)
    if tag.name == "p":
        return convert_p(tag)
    if tag.name == "table":
        return convert_table(tag)
    if tag.name == "img":
        return convert_img(tag)
    if tag.name == "a":
        return convert_a(tag)
    if tag.name == "ul":
        return convert_ul_ol(tag, True)
    if tag.name == "pre":
        return convert_pre(tag)
    if tag.name == "b":
        return convert_b(tag)
    if tag.name == "i":
        return convert_i(tag)
    if tag.name == "span":
        # span same as div -> just process children (no linebreaks)
        return convert_div(tag)
    if tag.name == "h1" or tag.name == "h2" or tag.name == "h3" or tag.name == "h4" or tag.name == "h5" or tag.name == "h6":
        return convert_header(tag)
    if tag.name == "ol":
        return convert_ul_ol(tag, False)
    if tag.name == "strong": 
        # use bold for strong
        return convert_b(tag)
    if tag.name == "u":
        return convert_u(tag)
    if tag.name == "em": 
        # use italic for em
        return convert_i(tag)
    if tag.name == "blockquote":
        return convert_blockquote(tag)
    if tag.name == "map":
        return convert_map(tag)
    if tag.name == "code":
        return convert_code(tag)
    if tag.name == "hr":
        return convert_hr(tag)
    if tag.name == "br":
        return convert_br(tag)
    if tag.name == "del" or tag.name == "s":
        return convert_strikethrough(tag)
    
    # Process children for unknown tags
    md = ""
    for child in tag.children:
        md += convert_html_tag(child)
    return md

def convert_header(tag):
    result = ""
    result += linebreak()
    
    if tag.name == "h1":
        result += "# "
    if tag.name == "h2":
        result += "## "
    if tag.name == "h3":
        result += "### "
    if tag.name == "h4":
        result += "#### "
        
    for child in tag.children:
        if child.__class__ == NavigableString:
            result += child.string
        # there may be inner tags for anchors. Not only <img>, but e.g. also <b> (bold text) etc:
        else:
            result += convert_html_tag(child)
    
    result += linebreak()
            
    return result

def convert_div(tag):
    
    # ignore Confluence meta-data divs:
    # try-catch id-attr
    try:
        if tag.id == "footer":
            # ignore "generate by Confluence" etc
            return ""
    except:
        pass
    # try-catch class-attr
    try:
        if tag.get("class") == "page_metadata":
            # ignore "Created by <user>"
            return ""
        if tag.get("class") == "pageSection group":
            # ignore attachments footer
            return ""
    except:
        pass
    
    md = ""
    for child in tag.children:
        if child.__class__ == NavigableString:
            md += child.string
        else:
            md += convert_html_tag(child)
    return md

def convert_p(tag):
    md = ""
    md += linebreak()

    # How to add text in <p>text</p>?
    # - tag.text does not work: returns text of ALL children
    # - tag.string does not work: fails if there are other tags, e.g. as in <p>text<br/>more text</p>
    # So, instead traverse children and check for string or tag.
    for child in tag.children:
        # print("convert_p:child:"+(str(type(child))))
        if child.__class__ == NavigableString:
            md += child.string
            # print("NavigableString: "+child.string)
        elif child.__class__ == Tag:
            if child.name == "br":
                # print("tag-br")
                md += linebreak()
            else:
                md += convert_html_tag(child)
        else:
            md += convert_html_tag(child)
    
    # linebreak at end of tag
    md += linebreak()
    
    return md

def convert_br(tag):
    # md = ""
    # in most cases, an additional linebreak looks worse than none (would cause
    # lots of empty lines, e.g. in lists etc). So, just skip <br> and return empty string
    # md += linebreak()
    return ""

def convert_table(tag):
    # in markdown, tables can be represented with pipes:
    # Col1 | Col2 ...
    # or by just rendering html. As complex tables (e.g. with multi-line-code) does not work
    # with pipe-rendering, just keep the html-table as-is:
    md = ""
    md += linebreak()

    # set rendering_html, so that other tag-processing works fine. E.g. <br/> will be kept as
    # <br/> instead of being converted to \n
    global rendering_html
    rendering_html = True
    # just keep the <html>-table as-is:
    md += str(tag)
    # add linebreaks
    md = md.replace('<tbody>', '<tbody>\n\n')
    md = md.replace('<tr>', '<tr>\n')
    md = md.replace('</th>', '</th>\n')
    md = md.replace('</td>', '</td>\n')
    md = md.replace('</tr>', '</tr>\n\n')
    # remove confluence-CSS
    md = md.replace(' class="confluenceTd"', '')
    md = md.replace(' class="confluenceTr"', '')
    md = md.replace(' class="confluenceTh"', '')
    md = md.replace(' class="confluenceTable"', '')
    md = md.replace(' colspan="1"', '')
    rendering_html = False

    # linebreak at end of tag
    md += linebreak()
    md += linebreak()
    
    return md

def convert_img(tag):
    # render img as html. Why? Cause markdown has no official/working
    # image-size-support (which i do require for markdown wiki)
    
    # Check for Confluence image macro
    if tag.name == "ac:image":
        # Extract image filename from attachment
        attachment = tag.find("ri:attachment")
        if attachment and attachment.has_attr("ri:filename"):
            filename = attachment["ri:filename"]
            alt_text = "Image"
            
            # Try to get alt text
            if tag.has_attr("ac:alt"):
                alt_text = tag["ac:alt"].replace(".png", "").replace(".jpg", "").replace(".jpeg", "").replace(".gif", "")
            
            # Return markdown image syntax with path to _attachments folder
            return f"![{alt_text}](_attachments/{filename})"
    
    # Handle standard HTML img tag
    src = tag.get("src", "")
    alt = tag.get("alt", "Image")
    
    # If it's a relative path, assume it's in the _attachments folder
    if src and not (src.startswith("http://") or src.startswith("https://")):
        if not src.startswith("_attachments/"):
            src = f"_attachments/{src}"
    
    return f"![{alt}]({src})"
    
def convert_a(tag):
    
    # return html as-is
    if rendering_html:
        return str(tag)

    # convert to markdown:
    # first split href-attr and text
    md = ""
    # default href = # to prevent exception due to None
    href = tag.get("href","#")
    text = ""
    for child in tag.children:
        if child.__class__ == NavigableString:
            text += child.string
        # there may be inner tags for anchors. Not only <img>, but e.g. also <b> (bold text) etc:
        else:
            text += convert_html_tag(child)
    
    # note: always render anchor-links inline. Even though markdown supports link-references (rendering
    # all links at end of page), github has issues/bugs with local/relative link-references. Whereas 
    # inline-version of same links does work.
    return "[" + text + "](" + href + ")"

    return md

def convert_pre(tag):
    # pre-tag -> source code
    md = ""
    md += linebreak()

    # Confluence uses "brush" for a specified language, e.g. <pre class="brush: bash; gutter: ...
    # Note: in bs4, tag-attributes which are expected to be multi-valued (such as 'class'),
    # will return a list of values EVEN if there are colon-/semicolon values: i.e. 'brush: bash' will
    # be returned as two values
    lang = ""
    class_value_list = tag.get('class',None)
    if class_value_list is not None:
        for idx, val in enumerate(class_value_list):
            if val == "brush:":
                # next value after brush is language. Remove last char via :-1
                lang = (class_value_list[idx+1])[:-1]
                break

    # add language-notification via HTML-comment as used on stackoverflow. This is ignored on 
    # github anyway (just a comment):
    if lang != "":
        md += "<!-- language: lang-" + lang + " -->"
        md += linebreak()
 
    # use github-flavored markdown (three backticks): 
    md += "```" + lang
    md += linebreak()
    
    for child in tag.children:
        if child.__class__ == NavigableString:
            md += child.string
    
    md += linebreak()
    md += "```"
    md += linebreak()
    return md

# convert lists, <ul> or <ol>
def convert_ul_ol(tag, isUl):
    md = ""
    # insert linebreaks around <ul>, but NOT for nested <ul>. Therefore, linebreak
    # only if indent-level is -1:
    global indent
    global li_for_ul_only
    global list_nr
    #if indent == -1:
    if not li_for_ul_only:
        md += linebreak()
    # increase indention for each list level
    indent += 1
    list_nr += 1
    for child in tag.children:
        if child.__class__ == Tag:
            if child.name == "li":
                md += convert_li(child, isUl)
    # reset indention
    indent -= 1
    list_nr -= 1
    if indent == -1:
        md += linebreak()
    return md

def convert_li(tag, isUl):
    # each <li> is prefixed with a dash
    md = ""
    global indent
    global li_break
    global list_nr
    # reset li_break, see end of function
    li_break = False
    # true if current <li> exist for purpose of single <ul> only, as in "<li><ul><li>content</li></ul></li>
    global li_for_ul_only
    # reset li_for_ul_only, might be True from previous nested list-element
    li_for_ul_only = False
    
    # check if current <li> exist for purpose of single <ul> only, as in "<li><ul><li>content</li></ul></li>
    if len(tag.contents)==1 and tag.contents[0].__class__ == Tag and tag.contents[0].name == "ul":
        li_for_ul_only = True

    # indent markup depending on level
    if not li_for_ul_only:
        for i in range(0,indent*2):
            md += " "
        if isUl is True:
            md += "- "
        else:
            md += str(list_nr) + " "

    # traverse children: append strings, delegate tag processing
    for child in tag.children:
        if child.__class__ == NavigableString:
            # a string, just append it
            md += child.string
        elif child.__class__ == Tag:
            md += convert_html_tag(child)
    
    # Linebreak after <li>. Skip if last chars in "md" already were li-break, as in </li></ul></li>.
    if not li_break and not li_for_ul_only:
        md += linebreak()
        li_break = True

    return md

# <b> bold tag
def convert_b(tag):
    # use ** for bold text (markdown also supports __, but ** better distincts from list dash -
    md = "**"
    for child in tag.children:
        if child.__class__ == NavigableString:
            md += child.string
    md += "**"
    return md

# <i> italic tag
def convert_i(tag):
    # use * for italic text (markdown also supports _, but * better distincts from list dash -
    md = "*"
    for child in tag.children:
        if child.__class__ == NavigableString:
            md += child.string
    md += "*"
    return md

# <u> tag
def convert_u(tag):
    # there is no underline in markdown. Emphasize with bold text instead
    md = "**"
    for child in tag.children:
        if child.__class__ == NavigableString:
            md += child.string
    md += "**"
    return md

# <blockquote> tag
def convert_blockquote(tag):
    # Process children with blockquote prefix
    md = ""
    for child in tag.children:
        content = convert_html_tag(child)
        if content:
            # Add blockquote prefix to each line
            lines = content.split('\n')
            md += '\n'.join([f"> {line}" if line.strip() else ">" for line in lines])
            md += "\n"
    return md

# <map> tag
def convert_map(tag):
    # TODO
    return "" 

# <code> tag
def convert_code(tag):
    md = "" 
    md += linebreak()
    md += "```"
    md += linebreak()
    return md

# <hr> tag, horizontal line
def convert_hr(tag):
    # there is no hr equivalent in markdown. Ignore, just add some space
    md = "" 
    md += linebreak()
    md += linebreak()
    return md

# Add support for Confluence task lists
def convert_task_list(tag):
    md = ""
    tasks = tag.find_all("ac:task")
    
    for task in tasks:
        status = task.find("ac:task-status")
        body = task.find("ac:task-body")
        
        if status and body:
            is_complete = status.string == "complete"
            task_text = "".join(str(c) for c in body.contents).strip()
            
            # Clean up any HTML tags in the task text
            soup = BeautifulSoup(task_text, 'html.parser')
            task_text = soup.get_text().strip()
            
            # Format as markdown task list item
            checkbox = "[x]" if is_complete else "[ ]"
            md += f"- {checkbox} {task_text}\n"
    
    return md + "\n"

# Add support for Confluence macros (callouts, code blocks, etc.)
def convert_structured_macro(tag):
    macro_name = tag.get("ac:name", "")
    
    # Handle code blocks
    if macro_name == "code":
        body = tag.find("ac:plain-text-body")
        if body and body.string:
            code = body.string
            # Try to determine language
            language = ""
            # Default to no language specification
            return f"```{language}\n{code}\n```\n"
    
    # Handle callouts/panels
    elif macro_name in ["note", "info", "tip", "warning"]:
        body = tag.find("ac:rich-text-body")
        if body:
            # Extract title and content
            paragraphs = body.find_all("p")
            title = ""
            content = ""
            
            if paragraphs and len(paragraphs) > 0:
                title = paragraphs[0].get_text().strip()
                
                # Get remaining content
                if len(paragraphs) > 1:
                    content = "\n".join([p.get_text().strip() for p in paragraphs[1:]])
            
            # Map Confluence macro types to Markdown callout types
            callout_type = "NOTE"
            if macro_name == "warning":
                callout_type = "WARNING"
            elif macro_name == "tip":
                callout_type = "SUCCESS"
            
            # Format as Obsidian-style callout
            return f"> [!{callout_type}] {title}\n> {content}\n\n"
    
    # Default handling for unknown macros
    return ""

# Add support for strikethrough
def convert_strikethrough(tag):
    md = "~~"
    for child in tag.children:
        md += convert_html_tag(child)
    md += "~~"
    return md

# convert the whole page / html_content. Taverses children and delegates logic per tag.
def convert_html_page(html_content):
    # let bs4 parse the html:
    soup = BeautifulSoup(html_content, "html.parser")
    # the markdown string returned as result:
    md = ""
    
    # html-page title: Confluence uses "spacename : pagename". Remove the spacename here
    global title
    title = soup.title.string 
    position_colon = title.find(" : ")
    if position_colon >= 0 :
        title = title[(position_colon+3):]
    md += "# " + title + md_dbr
    
    # goto <body><div id="main-content"> and ignore all that other Confluence-added-garbage
    div_main = soup.find("div", {"id": "main-content"})
    if div_main is None :
        return md
    # traverse all children of div_main and try to convert to markdown
    for child in div_main.children:
        md += convert_html_tag(child)

    return md

# Confluence sometimes has cryptic filenames, just consisting of digits. In that case, 
# the parsed title is used instead of the original filename. If filename already has 
# a string name, it is just returned.
def getMarkdownFilename(filename):
    if filename.isdigit():
       titleFilename = title
       titleFilename = titleFilename.replace(" ", "-")
       titleFilename = titleFilename.replace("++", "pp")
       titleFilename = titleFilename.replace("/", "")
       titleFilename = titleFilename.replace("+", "")
       titleFilename = titleFilename.replace("_", "-")
       titleFilename = titleFilename.replace("---", "-")
       titleFilename = titleFilename.replace("--", "-")
       
       print("Renaming:", filename, " -> ", title, " -> ", titleFilename)
       return titleFilename
    else:
       return filename

def convert_html_content(html_content):
    """
    Convert HTML content to Markdown.
    
    Args:
        html_content (str): The HTML content to convert.
        
    Returns:
        str: The converted Markdown content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the content
    content = ""
    
    # Find all headings, paragraphs, divs, etc.
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'table', 'pre', 'code', 'ul', 'ol', 'li']):
        content += convert_html_tag(tag)
    
    return content

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert Confluence HTML to Markdown.')
    parser.add_argument('source', help='Source directory containing HTML files')
    parser.add_argument('dest', help='Destination directory for Markdown files')
    args = parser.parse_args()
    
    # Check if source is a file or directory
    source_path = Path(args.source)
    if source_path.is_file() and source_path.suffix.lower() == '.html':
        # Convert a single HTML file
        with open(source_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        markdown_content = convert_html_page(html_content)
        
        # Write the Markdown content to the destination
        dest_path = Path(args.dest)
        if dest_path.suffix.lower() != '.md':
            dest_path = dest_path / (source_path.stem + '.md')
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Converted {source_path} to {dest_path}")
    else:
        # Convert all HTML files in the source directory
        shutil.copytree(args.source, args.dest)
        
        for html_file in Path(args.dest).glob('**/*.html'):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            markdown_content = convert_html_page(html_content)
            
            # Write the Markdown content to a new file
            markdown_file = html_file.with_suffix('.md')
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Remove the HTML file
            html_file.unlink()
        
        print(f"Converted all HTML files in {args.source} to Markdown in {args.dest}")



