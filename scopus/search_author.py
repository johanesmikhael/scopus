import hashlib
import os
from collections import namedtuple

from scopus.classes import Search

AUTHOR_SEARCH_DIR = os.path.expanduser('~/.scopus/author_search')

if not os.path.exists(AUTHOR_SEARCH_DIR):
    os.makedirs(AUTHOR_SEARCH_DIR)


class AuthorSearch(Search):
    @property
    def authors(self):
        """A list of namedtuples storing author information,
        where each namedtuple corresponds to one author.
        The information in each namedtuple is (eid surname initials givenname
        documents affiliation affiliation_id city country areas).

        All entries are strings or None.  Areas combines abbreviated subject
        areas followed by the number of documents in this subject.
        """
        out = []
        order = 'eid surname initials givenname affiliation documents '\
                'affiliation_id city country areas'
        auth = namedtuple('Author', order)
        for item in self._json:
            name = item.get('preferred-name', {})
            aff = item.get('affiliation-current', {})
            fields = item.get('subject-area',
                              [{'@abbrev': '', '@frequency': ''}])
            if isinstance(fields, dict):
                fields = [fields]
            areas = ["{} ({})".format(d.get('@abbrev', ''), d.get('@frequency', ''))
                     for d in fields]
            new = auth(eid=item['eid'],
                       surname=name.get('surname'),
                       initials=name.get('initials'),
                       givenname=name.get('given-name'),
                       documents=item.get('document-count', '0'),
                       affiliation=aff.get('affiliation-name'),
                       affiliation_id=aff.get('affiliation-id'),
                       city=aff.get('affiliation-city'),
                       country=aff.get('affiliation-country'),
                       areas="; ".join(areas))
            out.append(new)
        return out

    def __init__(self, query, count=200, start=0,
                 max_entries=5000, refresh=False):
        """Class to search a query, and retrieve a list of author IDs as results.

        Parameters
        ----------
        query : str
            A string of the query, e.g. "authlast(Einstein) and
            authfirst(Albert)".

        count : int (optional, default=200)
            The number of entries to be displayed at once.  A smaller number
            means more queries with each query having less results.

        start : int (optional, default=0)
            The entry number of the first search item to start with.

        refresh : bool (optional, default=False)
            Whether to refresh the cached file if it exists or not.

        max_entries : int (optional, default=5000)
            Raise error when the number of results is beyond this number.
            The Scopus Search Engine does not allow more than 5000 entries.

        Raises
        ------
        Exception
            If the number of search results exceeds max_entries.

        Notes
        -----
        Json results are cached in ~/.scopus/author_search/{fname}, where
        fname is the hashed version of query.

        The results are stored as a property named authors.
        """

        self.query = query
        qfile = os.path.join(AUTHOR_SEARCH_DIR,
                             hashlib.md5(query.encode('utf8')).hexdigest())
        url = 'https://api.elsevier.com/content/search/author'
        Search.__init__(self, query, qfile, url, refresh, count, start,
                        max_entries)

    def __str__(self):
        s = """{query}
        Resulted in {N} hits.
    {entries}"""
        return s.format(query=self.query, N=len(self._json),
                        entries='\n    '.join([str(a) for a in self._json]))
