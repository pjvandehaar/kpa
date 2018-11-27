import shutil

def _not_empty(iterable):
    try:
        next(iterable)
        return True
    except StopIteration:
        return False

def repr_node(node):
    if isinstance(node, str): return repr(node)
    ret = f'<{node.name}'
    if 'id' in node.attrs: ret += f' id="{node.attrs["id"]}"'
    if 'class' in node.attrs: ret += f' class="{" ".join(node.attrs["class"])}"'
    for k,v in node.attrs.items():
        if k not in ('id','class'): ret += f' {k}="{v}"'
    return ret + '>'

def render_tree(node, depth=1):
    ret = repr_node(node)
    if isinstance(node, bs4.element.Tag) and _not_empty(node.children):
        if depth >= 1:
            for child in node.children:
                for line in render_tree(child, depth=depth-1).split('\n'): ret += '\n   ' + line
        else:
            num_descendants = sum(1 for _ in node.descendants)
            ret += f'\n   ... {num_descendants}'
    return ret

def print_tree(node, depth=1, maxwidth=None):
    if maxwidth is None: maxwidth = shutil.get_terminal_size().columns
    if maxwidth == 0: maxwidth = 1_000_000_000
    print('\n'.join(line[:maxwidth] for line in render_tree(node, depth).split('\n')))

if __name__ == '__main__':
    from bs4 import BeautifulSoup; import bs4, lxml
    from kpa.http_utils import cached_get
    soup = BeautifulSoup(cached_get('https://google.com').text, 'lxml')
    print_tree(soup.select_one('html'), depth=3)
