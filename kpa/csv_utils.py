#!/usr/bin/env python3

import csv, io
from typing import List,Dict,TextIO,Iterable


def write_tsv(filename:str, data:Iterable[dict]) -> None:
    with open(filename, 'wt') as f:
        write_tsv_to_fileobj(data, f)

def as_tsv(data:Iterable[dict]) -> str:
    stream = io.StringIO()
    write_tsv_to_fileobj(data, stream)
    return stream.getvalue()

def write_tsv_to_fileobj(data:Iterable[dict], writer:TextIO) -> None:
    # TODO: Reduce RAM by gathering keys from first 10k rows, and hoping that remaining rows have same keys.
    data = [{str(key):val for key,val in row.items()} for row in data]
    colnames = []
    for row in data:
        for colname in row.keys():
            if colname not in colnames: colnames.append(colname)
    writer.write('\t'.join(colnames) + '\n')
    for row in data: writer.write('\t'.join(str(row.get(colname,'')) for colname in colnames) + '\n')


def print_table(data:Iterable[dict], gutter:str='  ') -> None:
    if isinstance(gutter,int): gutter = ' '*gutter
    data = [{str(key):str(val) for key,val in row.items()} for row in data]
    colwidths: Dict[str,int] = {}
    for row in data:
        for colname in row.keys():
            colwidths[colname] = max(colwidths.get(colname,0), len(row[colname]))
    for colname in colwidths:
        colwidths[colname] = max(colwidths[colname], len(colname))
    print(gutter.join(f'{colname:{colwidth}}' for colname,colwidth in colwidths.items()))
    for row in data:
        print(gutter.join(f'{row.get(colname,""):{colwidth}}' for colname,colwidth in colwidths.items()))


def read_tsv(filename:str) -> Iterable[Dict[str,str]]:
    with open(filename) as f:
        header = next(f).rstrip('\n').split('\t')
        assert header, header
        header[0] = header[0].lstrip('#')
        for line in f:
            row = line.rstrip('\n').split('\t')
            assert len(header) == len(row), (len(header), len(row), header, row)
            yield dict(zip(header, row))



if __name__ == '__main__':
    print(as_tsv([
        dict(a=1,b=2,c_____=3),
        dict(a=4,    c_____=5),
        dict(a='foo',         d=6)]))

    print_table([
        dict(a=1,b=2,c_____=3),
        dict(a=4,    c_____=5),
        dict(a='foo',         d=6)])
