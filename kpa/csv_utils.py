
import csv, io
from typing import List,Dict,Any, TextIO, Iterable


def write_tsv(filename:str, data:Iterable[Dict[str,Any]]) -> None:
    with open(filename, 'wt') as f:
        write_tsv_to_fileobj(list(data), f)

def as_tsv(data:Iterable[Dict[str,Any]]) -> str:
    stream = io.StringIO()
    write_tsv_to_fileobj(list(data), stream)
    return stream.getvalue()

def write_tsv_to_fileobj(data:List[Dict[str,Any]], writer:TextIO) -> None:
    assert isinstance(data, list) and all(isinstance(row, dict) for row in data), data
    assert all(isinstance(colname, str) for row in data for colname in row.keys()), data
    colnames = []
    for row in data:
        for colname in row.keys():
            if colname not in colnames: colnames.append(colname)
    writer.write('\t'.join(colnames) + '\n')
    for row in data: writer.write('\t'.join(str(row.get(colname,'')) for colname in colnames) + '\n')


if __name__ == '__main__':
    print(as_tsv([
        dict(a=1,b=2,c=3),
        dict(a=1,    c=3),
        dict(            d=4)]))
